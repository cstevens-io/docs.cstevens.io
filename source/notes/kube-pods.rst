Kubernetes pods
===============

Create and run a pod named my-nginx-pod
---------------------------------------

.. code-block:: text

    $ kubectl run my-nginx-pod -it --image nginx -- sh

Delete the my-nginx-pod pod you just created
--------------------------------------------

.. code-block:: text

    $ kubectl delete pod my-nginx-pod

Create pod then delete after it finishes running
------------------------------------------------

.. code-block:: text

    $ kubectl run my-nginx-pod -it --rm --image nginx -- sh

Access the nginx pod you created
--------------------------------

.. code-block:: text

    $ kubectl port-forward my-nginx-pod 8080:80
      <browse to localhost:8080>

View logs of the nginx pod
--------------------------

.. code-block:: text

    $ kubectl logs my-nginx-pod
