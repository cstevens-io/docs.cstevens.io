k3s, traefik and ingress
========================

Special thanks to `just me and open source <https://www.youtube.com/user/wenkatn>`_, specifically `this video <https://www.youtube.com/watch?v=12taKl5iCpA>`_

.. code-block:: text

   # install k3s
   curl -sfL https://get.k3s.io | sh -

   # traefik comes as a deployment
   kubectl -n kube-system get deploy

   # let's enable the traefik dashboard
   # notice traefik has a configmap named traefik
   kubectl -n kube-system describe deploy traefik

   # edit the configmap
   kubectl -n kube-system edit cm traefik
   # we need to add under traefik.toml:
   [api]
     dashboard = true

   # you can reload the pod to re-read the config by scaling the deployment
   # or you can simply delete the pod and let the replicaset start a new one
   kubectl -n kube-system scale deploy traefik --replicas 0
   kubectl -n kube-system scale deploy traefik --replicas 1
   # or
   kubectl -n kube-system delete pod traefikyyyyyyyyy-zzzzz

   # the traefik dashboard runs on port 8080 but only inside the cluster
   # so you'll have to use port-forward to access it (unless you want to expose
   # it outside of the cluster, we can talk about that later)
   # once you complete the below command, open up http://localhost:8080 in a browser
   kubectl -n kube-system port-forward deployment/traefik 8080

   # let's deploy nginx, expose it as a service, then create an ingress
   kubectl create deploy nginx --image nginx

   # verify you have an nginx deployment
   kubectl get deploy -o wide

   # expose the deployment
   kubectl expose deploy nginx --port 80

   # verify you have an nginx service
   kubectl get service

   # create an ingress resource
   # from the example here: https://github.com/rancher/k3d/blob/master/docs/usage/guides/exposing_services.md
   # create a nginx-ingress.yaml:
   apiVersion: extensions/v1beta1
   kind: Ingress
   metadata:
     name: nginx
     annotations:
       ingress.kubernetes.io/ssl-redirect: "false"
   spec:
     rules:
     - http:
         paths:
         - path: /
           backend:
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

   # let's add basic auth to the nginx site
   htpasswd -c ./authfile <username>
   kubectl create secret generic nginx-auth --from-file authfile
   kubectl get secret nginx-auth -o yaml

   # then in the nginx-ingress.yaml file, add annotations under metadata:
   metadata:
     annotations:
       kubernetes.io/ingress.class: traefik
       ingress.kubernetes.io/auth-type: "basic"
       ingress.kubernetes.io/auth-realm: "nginx-auth"

   # then delete and re-create the nginx ingress resource
   kubectl delete -f nginx-ingress.yaml
   kubectl create -f nginx-ingress.yaml
