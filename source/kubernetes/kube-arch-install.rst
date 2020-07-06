Install Kubernetes on Arch
==========================

.. Mostly stolen from `StephenSorriaux's gist <https://gist.github.com/StephenSorriaux/fa07afa57c931c84d1886b08c704acfe>`_

.. note::

    This is not a step-by-step installation guide for beginners.  This article assumes you have some previous experience with Linux and Kubernetes.

Install some needed utilities
-----------------------------

.. code-block:: text

    # pacman -S conntrack-tools docker ebtables ethtool socat

Disable swap space
------------------

.. code-block:: text

    # swapoff -a
    # sed -e '/swap/ s/^#*/#/' -i /etc/fstab

Load and configure the br_netfilter module
------------------------------------------

.. code-block:: text

    # modprobe br_netfilter
    # sysctl net.bridge.bridge-nf-call-iptables=1
    # echo "br_netfilter" > /etc/modules-load.d/br_netfilter.conf
    # echo "net.bridge.bridge-nf-call-iptables=1" > /etc/sysctl.d/br_netfilter.conf

Update the `ExecStart` line in the docker unit file
---------------------------------------------------

.. code-block:: text
    :caption: /usr/lib/systemd/system/docker.service

    ExecStart=/usr/bin/dockerd --exec-opt native.cgroupdriver=systemd --iptables=false --ip-masq=false -H fd:// 

Start and enable docker
-----------------------

.. code-block:: text
    
    # systemctl daemon-reload
    # systemctl enable docker
    # systemctl start docker

Download the latest kubernetes binaries
---------------------------------------

.. code-block:: text

    # RELEASE="$(curl -sSL https://dl.k8s.io/release/stable.txt)"
    # ARCH="amd64"
    # cd /usr/local/bin
    # curl -L --remote-name-all https://storage.googleapis.com/kubernetes-release/release/${RELEASE}/bin/linux/${ARCH}/{kubeadm,kubelet,kubectl}
    # chmod +x {kubeadm,kubelet,kubectl} && cd
    # mkdir -p /etc/systemd/system/kubelet.service.d

Download the latest container network interface
-----------------------------------------------

.. code-block:: text

    CNI_VERSION="v0.8.6"
    mkdir -p /opt/cni/bin
    curl -L "https://github.com/containernetworking/plugins/releases/download/${CNI_VERSION}/cni-plugins-linux-amd64-${CNI_VERSION}.tgz" | tar -C /opt/cni/bin -xz

Download the latest container runtime interface
-----------------------------------------------

.. code-block:: text

    CRICTL_VERSION="v1.18.0"
    mkdir -p /opt/cri
    curl -L "https://github.com/kubernetes-incubator/cri-tools/releases/download/${CRICTL_VERSION}/crictl-${CRICTL_VERSION}-linux-amd64.tar.gz" | tar -C /opt/cri -xz


Create systemd unit files for kubelet
-------------------------------------

.. code-block:: text
    :caption: /etc/systemd/system/kubelet.service

    [Unit]
    Description=kubelet: The Kubernetes Node Agent
    Documentation=http://kubernetes.io/docs/
    Wants=network-online.target
    After=network-online.target

    [Service]
    ExecStart=/usr/local/bin/kubelet
    Restart=always
    StartLimitInterval=0
    RestartSec=10

    [Install]
    WantedBy=multi-user.target 

.. code-block:: text
    :caption: /etc/systemd/system/kubelet.service.d/10-kubeadm.conf

    # Note: This dropin only works with kubeadm and kubelet v1.11+
    [Service]
    Environment="KUBELET_KUBECONFIG_ARGS=--bootstrap-kubeconfig=/etc/kubernetes/bootstrap-kubelet.conf --kubeconfig=/etc/kubernetes/kubelet.conf"
    Environment="KUBELET_CONFIG_ARGS=--config=/var/lib/kubelet/config.yaml"
    # This is a file that "kubeadm init" and "kubeadm join" generates at runtime, populating the KUBELET_KUBEADM_ARGS variable dynamically
    EnvironmentFile=-/var/lib/kubelet/kubeadm-flags.env
    # This is a file that the user can use for overrides of the kubelet args as a last resort. Preferably, the user should use
    # the .NodeRegistration.KubeletExtraArgs object in the configuration files instead. KUBELET_EXTRA_ARGS should be sourced from this file.
    EnvironmentFile=-/etc/default/kubelet
    ExecStart=
    ExecStart=/usr/local/bin/kubelet $KUBELET_KUBECONFIG_ARGS $KUBELET_CONFIG_ARGS $KUBELET_KUBEADM_ARGS $KUBELET_EXTRA_ARGS

Enable and start kubelet
------------------------

.. code-block:: text

    # systemctl enable kubelet
    # systemctl start kubelet

Initialize the cluster
----------------------

Master node:

.. code-block:: text

    # kubeadm init --pod-network-cidr=10.244.0.0/16

Worker node:

.. code-block:: text

    # kubeadm join 192.168.1.241:6443 --token <token> --discovery-token-ca-cert-hash sha256: <hash>
 

Setup kubectl config
--------------------

.. code-block:: text

    $ mkdir -p $HOME/.kube
    $ cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    $ chown $(id -u):$(id -g) $HOME/.kube/config

Deploy a pod network to the cluster
-----------------------------------

.. code-block:: text

    Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
    https://kubernetes.io/docs/concepts/cluster-administration/addons/
    eg:
    kubectl apply -f "https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d '\n')"

Add kubectl completion and alias
--------------------------------

.. code-block:: text

    cat >>~/.zshrc<<EOF
    source <(kubectl completion zsh)
    alias k=kubectl
    complete -F __start_kubectl k
    EOF

kubectl examples
----------------

.. list-table::
    :widths: 25 75

    * - **Command**
      - **Description**
    * - kubectl get nodes
      - List all nodes in the cluster
    * - kubectl get all -A
      - Show all resources from all namespaces
    * - kubectl describe nodes
      - Show information of all nodes in the cluster
    * - kubectl top node
      - Get node resource usage
    * - kubectl top pod
      - Get pod resource usage
