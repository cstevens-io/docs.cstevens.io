k3s, traefik2 and ingress
=========================

Special thanks to `just me and open source <https://www.youtube.com/user/wenkatn>`_, specifically `this video <https://www.youtube.com/watch?v=12taKl5iCpA>`_

.. code-block:: text

   # install k3s wihout traefik v1
   curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server --disable traefik" sh

   # put this in a file /var/lib/rancher/k3s/server/manifests/traefik2.yaml
   apiVersion: helm.cattle.io/v1
   kind: HelmChart
   metadata:
     name: traefik
     namespace: kube-system
   spec:
     chart: traefik
     repo: https://containous.github.io/traefik-helm-chart
     set:
       image.tag: "2.2"

   # then reload k3s
   systemctl restart k3s

   # watch and you'll see it create traefik pods, deployment and a service
   kubectl -n kube-system get all

   # edit the traefik deployment to enable api.insecure
   # this allows us to see the traefik v2 dashboard outside the cluster
   # without accessing it through an ingress
   kubectl -n kube-system edit deploy traefik

   # add the following line in the appropriate spot
   - --api.insecure=true

   # you can reload the pod to re-read the config by scaling the deployment
   # or you can simply delete the pod and let the replicaset start a new one
   kubectl -n kube-system scale deploy traefik --replicas 0
   kubectl -n kube-system scale deploy traefik --replicas 1
   # or
   kubectl -n kube-system delete pod traefikyyyyyyyyy-zzzzz

   # edit the traefik service and add port 9000
   kubectl -n kube-system edit service traefik
   - name: traefik
    nodePort: 32323
    port: 9000
    protocol: TCP
    targetPort: traefik

   # the traefik dashboard runs on port 8080 but only inside the cluster
   # so you'll have to use port-forward to access it (unless you want to expose
   # it outside of the cluster, we can talk about that later)
   # once you complete the below command, open up http://localhost:8080 in a browser
   # kubectl -n kube-system port-forward deployment/traefik 8080:9000

   # create an ingress for traefik2 dashboard
   apiVersion: extensions/v1beta1
   kind: Ingress
   metadata:
     name: "traefik-dash-ingress"
     namespace: kube-system
   spec:
     rules:
       - host: traefik-dash.lab.pwned.com
         http:
           paths:
             - backend:
                 serviceName: traefik
                 servicePort: 9000

   # let's deploy nginx, expose it as a service, then create an ingress
   kubectl create deploy nginx --image nginx

   # verify you have an nginx deployment
   kubectl get deploy -o wide

   # expose the deployment
   kubectl expose deploy nginx --port 80

   # verify you have an nginx service
   kubectl get service

   # create a file for nginx ingress resource

   apiVersion: extensions/v1beta1
   kind: Ingress
   metadata:
     name: nginx
   spec:
     rules:
     - host: common.lab.pwned.com
     - http:
         paths:
           - backend:
               serviceName: nginx
               servicePort: 80

   kubectl create -f nginx-ingress.yaml

   kubectl get ingress
   kubectl describe ingress nginx

   # backend IP should match nginx pod
   kubectl get pods -o wide

   # browse to any cluster IP http://192.168.1.211
   # should bring up nginx welcome page
   # now browse back to the dashboard (make sure you're still port-forwarded)
   # http://localhost:8080
   # and you will see traefik populate a front-end and a back-end
