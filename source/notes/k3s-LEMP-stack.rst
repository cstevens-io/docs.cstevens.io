LEMP the Kubernetes way
=======================

In an effort to tie together a bunch of k8s stuff I've learned, I decided to install some forum software and configure it the "k8s way".  That is, a pod for each service: nginx, php-fpm and MySQL, as well as a kube service for each, each tied to a deployment for scaling and availability.  I chose http://phpbb.com since everyone knows it and it's well documented.  I also chose to use the local-path privisioner that comes with k3s for persistent storage for MySQL and for the html/php files for phpBB.  I am using traefik for ingress which, in turn, uses letsencrypt to fetch SSL certs.

First thing I did was create a namespace called ``forums`` to keep things organized:

.. code-block:: text
   :caption: namespace.yaml

   $ cat <<EOF > namespace.yaml
   apiVersion: v1
   kind: Namespace
   metadata:
     name: forums
   EOF
   $ kubectl create -f namespace.yaml
   $ kubectl get ns

Create some persistent storage for MySQL and the html/php files.  One thing I learned about the loca-path storage class is that it only works with access mode ReadWriteOnce, which when you read up on it, people say "Only one pod can mount this persistent volume at a time."  That's not entirely true.  So long as the pods are on the same node, any pod can mount this volume.  Which is a good thing, else how would I scale up the web servers unless I put the html files in the container?

.. code-block:: text
   :caption: pvc.yaml

   $ cat <<EOF > pvc.yaml
   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: mysql-pvc
     namespace: forums
   spec:
     accessModes:
     - ReadWriteOnce
     storageClassName: local-path
     resources:
       requests:
         storage: 5Gi
   ---

   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: html-pvc
     namespace: forums
   spec:
     accessModes:
     - ReadWriteOnce
     storageClassName: local-path
     resources:
       requests:
         storage: 10Gi
   EOF
   $ kubectl create -f pvc.yaml
   $ kubectl -n forums get pvc

I created a root password for MySQL, so when we start the pod it can initialize itself, a MySQL service for reachability within the cluster and a MySQL pod which mounts persistent storage.  The root password is base64 encoded.  If you run it through ``base64 --decode`` you'll see the password is just ``password``

.. code-block:: text
   :caption: mysql.yaml

   $ cat <<EOF >mysql.yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: mysql-root-pass
     namespace: forums
   data:
     password: cGFzc3dvcmQ=
   ---
   
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: mysql
     namespace: forums
     labels:
       app: mysql
       tier: back
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: mysql
     template:
       metadata:
         labels:
           app: mysql
       spec:
         containers:
         - name: mysql
           image: mariadb:10.5.4-focal
           imagePullPolicy: IfNotPresent
           volumeMounts:
           - name: mysql
             mountPath: /var/lib/mysql
           ports:
           - containerPort: 3306
           env:
           - name: MYSQL_ROOT_PASSWORD
             valueFrom:
               secretKeyRef:
                 name: mysql-root-pass
                 key: password
         volumes:
         - name: mysql
           persistentVolumeClaim:
             claimName: mysql-pvc
   ---
   
   apiVersion: v1
   kind: Service
   metadata:
     name: mysql
     namespace: forums
     labels:
       app: mysql
       tier: back
   spec:
     ports:
     - port: 3306
       protocol: TCP
       targetPort: 3306
     selector:
       app: mysql
   EOF
   $ kubectl create -f mysql.yaml

Getting the php contiainer working with ``mysqli`` wasn't easy.  I didn't have any luck at all when trying to exec into the container and running ``docker-php-ext-install mysqli``.  It seemed no matter how much I tried php wouldn't load the mysqli module after the pod was already running.  Restarting the pod (even with a ``reboot`` within the pod) just seemed to bring the php image back to its original state.  I had to do this externally with docker:

.. code-block:: text

   $ cat <<EOF Dockerfile >
   FROM php:alpine
   RUN docker-php-ext-install mysqli
   EOF
   $ docker build . -t splooge/php:latest
   $ docker login
   $ docker push

Now that I had a working php image with MySQL support on docker hub I was able to use that for the php service.

.. code-block:: text
   :caption: php.yaml

   cat <<EOF > php.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: php
     namespace: forums
     labels:
       app: php
       tier: middle
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: php
     template:
       metadata:
         labels:
           app: php
       spec:
         containers:
         - name: php
           image: splooge/php:latest
           imagePullPolicy: Always
           volumeMounts:
           - name: html-pvc
             mountPath: /var/www/html
           ports:
           - containerPort: 9000
         volumes:
         - name: html-pvc
           persistentVolumeClaim:
             claimName: html-pvc
   ---
   
   apiVersion: v1
   kind: Service
   metadata:
     name: php
     namespace: forums
     labels:
       app: php
       tier: middle
   spec:
     ports:
     - port: 9000
       protocol: TCP
       targetPort: 9000
     selector:
   app: php
   EOF
   $ kubectl create -f php.yaml
   $ kubectl -n forums get all

For nginx I created a ``configMap`` which allows us to store the nginx config within kubernetes and access that config when an nginx pod is spun up.  That config will be laid down on the filesystem during container creation before nginx starts up.  We're also going to mount the volume with the html to /var/www/html and point nginx to it.

.. code-block:: text
   :caption: nginx.yaml

   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: nginx-config
     namespace: forums
     labels:
       app: nginx
       tier: front
   data:
     config: |
       server {
         index index.php index.html;
         error_log /var/log/nginx/error.log;
         access_log /var/log/nginx/access.log;
         root /var/www/html;
   
         location /install/app.php {
           try_files $uri $uri/ /install/app.php?$query_string;
         }
   
         location / {
           try_files $uri $uri/ /index.php?$query_string;
         }
   
         location ~ \.php$ {
           try_files $uri = 404;
           fastcgi_split_path_info ^(.+\.php)(/.+)$;
           fastcgi_pass php:9000;
           fastcgi_index index.php;
           include fastcgi_params;
           fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
           fastcgi_param PATH_INFO $fastcgi_path_info;
         }
       }
   
   ---
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: nginx
     namespace: forums
     labels:
       app: nginx
       tier: front
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: nginx
     template:
       metadata:
         labels:
           app: nginx
       spec:
         containers:
         - name: nginx
           image: nginx
           imagePullPolicy: IfNotPresent
           volumeMounts:
           - name: html-pvc
             mountPath: /var/www/html
           - name: config
             mountPath: /etc/nginx/conf.d
           ports:
           - containerPort: 9000
         volumes:
         - name: html-pvc
           persistentVolumeClaim:
             claimName: html-pvc
         - name: config
           configMap:
             name: nginx-config
             items:
             - key: config
               path: site.conf
   ---
   
   apiVersion: v1
   kind: Service
   metadata:
     name: nginx
     namespace: forums
     labels:
       app: nginx
       tier: front
   spec:
     ports:
     - port: 80
       protocol: TCP
       targetPort: 80
     selector:
       app: nginx
   EOF
   $ kubectl create -f nginx.yaml
   $ kubectl -n forums get all

Finally we're going to create an ingressroute so traefik knows which service to send traffic destined for ``forums.pwned.com``.  You'll need to refer to other documents on this site to setup traefik to work with k3s.

.. code-block:: text
   :caption: ingressroute.yaml

   cat <<EOF > ingressroute.yaml
   apiVersion: traefik.containo.us/v1alpha1
   kind: IngressRoute
   metadata:
     name: forums.pwned.com
     namespace: forums
   spec:
     entryPoints:
       - web
       - websecure
     routes:
       - match: Host(`forums.pwned.com`)
         kind: Rule
         services:
           - name: nginx
             port: 80
     tls:
       certResolver: default
   EOF
   $ kubectl create -f ingressroute.yaml
   $ kubectl -n forums get all
   $ kubectl -n forums get pv,pvc,svc,deploy,rs,pod,ingressroute

Finally you'll need to download phpbb and extract it to your local filesystem where your html-pvc gets bound.  For local-path storage and k3s this will be under /var/lib/rancher/k3s/storage/pvc-[uuid]

We now have our forum software running at https://forums.pwned.com

You can scale out the nginx front-ends or the php-fpm servers by running:

.. code-block:: text

   $ kubectl -n forums scale deploy nginx --replicas 3
   $ kubectl -n forums scale deploy php --replicas 5

I wouldn't try to scale out the MySQL database, who knows what fun corruption you'll run into if you have 2+ instances of MySQL trying to write to the same files.

And here's the end result of all the kubernetes objects we created along the way:

.. code-block:: text

   $ kubectl -n forums get pv,pvc,svc,deploy,rs,pod,ingressroute
   NAME                                                        CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM              STORAGECLASS   REASON   AGE
   persistentvolume/pvc-2be3815d-c1ee-4112-9a0e-514997d61dff   10Gi       RWO            Delete           Bound    forums/html-pvc    local-path              20h
   persistentvolume/pvc-b2957d3c-80c3-4475-b1dc-e8253beb2042   5Gi        RWO            Delete           Bound    forums/mysql-pvc   local-path              20h
   
   NAME                              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
   persistentvolumeclaim/html-pvc    Bound    pvc-2be3815d-c1ee-4112-9a0e-514997d61dff   10Gi       RWO            local-path     20h
   persistentvolumeclaim/mysql-pvc   Bound    pvc-b2957d3c-80c3-4475-b1dc-e8253beb2042   5Gi        RWO            local-path     20h
   
   NAME            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
   service/mysql   ClusterIP   10.43.229.202   <none>        3306/TCP   20h
   service/php     ClusterIP   10.43.187.226   <none>        9000/TCP   14h
   service/nginx   ClusterIP   10.43.135.35    <none>        80/TCP     14h
   
   NAME                    READY   UP-TO-DATE   AVAILABLE   AGE
   deployment.apps/mysql   1/1     1            1           20h
   deployment.apps/php     1/1     1            1           14h
   deployment.apps/nginx   3/3     3            3           14h
   
   NAME                               DESIRED   CURRENT   READY   AGE
   replicaset.apps/mysql-69c67b54dd   1         1         1       20h
   replicaset.apps/php-7f5ff45fb8     1         1         1       14h
   replicaset.apps/nginx-75c9f895bd   3         3         3       14h
   
   NAME                         READY   STATUS    RESTARTS   AGE
   pod/mysql-69c67b54dd-sb56s   1/1     Running   0          20h
   pod/php-7f5ff45fb8-xsfbv     1/1     Running   0          14h
   pod/nginx-75c9f895bd-cnblf   1/1     Running   0          14h
   pod/nginx-75c9f895bd-hskfh   1/1     Running   0          12h
   pod/nginx-75c9f895bd-vdf6h   1/1     Running   0          12h
   
   NAME                                                AGE
   ingressroute.traefik.containo.us/forums.pwned.com   12h
