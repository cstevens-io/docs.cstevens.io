Kubernetes deployments
======================

Deployments create replicasets, replicasets manage pods

Create an nginx deployment
--------------------------

.. code-block:: text

    $ kubectl create deployment nginx --image nginx

Scale the deployment
--------------------

.. code-block:: text

    $ kubectl scale deployment nginx --replicas 2

Expose the deployment as a NodePort
-----------------------------------

.. code-block:: text

    $ kubectl expose deployment nginx --type NodePort --port 80

To access the nginx deployment use ``kubectl get service`` to find the NodePort then browse to ``http://<node>:<port>`` where <node> is the IP/hostname of any of the kubernetes nodes and <port> is the 5 digit port listed in the nginx service.
