Install Kubernetes on Arch in Vagrant
=====================================

Install homebrew package manager
--------------------------------

.. code-block:: text

   $ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

Install kubectl, vagrant, virtualbox
------------------------------------

.. code-block:: text

   $ brew install kubernetes-cli
   $ brew cask install vagrant
   $ brew cask install virtualbox

Create the following files
--------------------------

.. code-block:: text
   :caption: Vagrantfile

    # -*- mode: ruby -*-
    # vi: set ft=ruby :
    
    Vagrant.configure(2) do |config|
    
      config.vm.synced_folder '/host/path', '/guest/path', disabled: true
    
      config.vm.provision "shell", path: "bootstrap.sh"
    
      # Kubernetes Master Server
      config.vm.define "k8smaster001" do |k8smaster001|
        k8smaster001.vm.box = "archlinux/archlinux"
        k8smaster001.vm.hostname = "k8smaster001.lab.pwned.com"
        k8smaster001.vm.network "private_network", ip: "192.168.2.100"
        k8smaster001.vm.provider "virtualbox" do |v|
          v.name = "k8smaster001"
          v.memory = 2048
          v.cpus = 2
          # Prevent VirtualBox from interfering with host audio stack
          v.customize ["modifyvm", :id, "--audio", "none"]
        end
        k8smaster001.vm.provision "shell", path: "bootstrap_kmaster.sh"
      end
    
      NodeCount = 2

      # Kubernetes Worker Nodes
      (1..NodeCount).each do |i|
        config.vm.define "k8sworker00#{i}" do |workernode|
          workernode.vm.box = "archlinux/archlinux"
          workernode.vm.hostname = "k8sworker00#{i}.lab.pwned.com"
          workernode.vm.network "private_network", ip: "192.168.2.10#{i}"
          workernode.vm.provider "virtualbox" do |v|
            v.name = "k8sworker00#{i}"
            v.memory = 1024
            v.cpus = 1
            # Prevent VirtualBox from interfering with host audio stack
            v.customize ["modifyvm", :id, "--audio", "none"]
          end
          workernode.vm.provision "shell", path: "bootstrap_kworker.sh"
        end
      end
    
    end

.. code-block:: text
   :caption: bootstrap.sh

   #!/bin/bash

   # update hosts file
   echo "[TASK 1] update /etc/hosts file"
   cat >>/etc/hosts<<EOF
   192.168.2.100 k8smaster001.lab.pwned.com k8smaster001
   192.168.2.101 k8sworker001.lab.pwned.com k8sworker001
   192.168.2.102 k8sworker002.lab.pwned.com k8sworker002
   EOF

   echo "[TASK 2] install docker and tools"
   pacman --noconfirm -Sy
   pacman --noconfirm -S conntrack-tools docker ebtables ethtool socat sshpass

   echo "[TASK 3] load and configure br_netfilter module"
   modprobe br_netfilter
   echo "br_netfilter" > /etc/modules-load.d/br_netfilter.conf

   echo "[TASK 4] add sysctl settings"
   cat >>/etc/sysctl.d/kubernetes.conf<<EOF
   net.bridge.bridge-nf-call-ip6tables = 1
   net.bridge.bridge-nf-call-iptables = 1
   EOF
   sysctl --system >/dev/null 2>&1

   echo "[TASK 5] fix docker.service unit"
   rm /usr/lib/systemd/system/docker.service
   cat >>/usr/lib/systemd/system/docker.service<<EOF
   [Unit]
   Description=Docker Application Container Engine
   Documentation=https://docs.docker.com
   After=network-online.target docker.socket firewalld.service
   Wants=network-online.target
   Requires=docker.socket

   [Service]
   Type=notify
   # the default is not to use systemd for cgroups because the delegate issues still
   # exists and systemd currently does not support the cgroup feature set required
   # for containers run by docker
   ExecStart=/usr/bin/dockerd --exec-opt native.cgroupdriver=systemd --iptables=false --ip-masq=false -H fd://
   ExecReload=/bin/kill -s HUP $MAINPID
   LimitNOFILE=1048576
   # Having non-zero Limit*s causes performance problems due to accounting overhead
   # in the kernel. We recommend using cgroups to do container-local accounting.
   LimitNPROC=infinity
   LimitCORE=infinity
   # Uncomment TasksMax if your systemd version supports it.
   # Only systemd 226 and above support this version.
   #TasksMax=infinity
   TimeoutStartSec=0
   # set delegate yes so that systemd does not reset the cgroups of docker containers
   Delegate=yes
   # kill only the docker process, not all processes in the cgroup
   KillMode=process
   # restart the docker process if it exits prematurely
   Restart=on-failure
   StartLimitBurst=3
   StartLimitInterval=60s

   [Install]
   WantedBy=multi-user.target
   EOF

   echo "[TASK 6] enable docker service"
   systemctl enable docker >/dev/null 2>&1
   systemctl start docker

   echo "[TASK 7] disable and turn off swap"
   sed -i '/swap/d' /etc/fstab
   swapoff -a

   echo "[TASK 8] download latest kubernetes binaries"
   RELEASE="$(curl -sSL https://dl.k8s.io/release/stable.txt)"
   ARCH="amd64"
   cd /usr/local/bin
   curl -sL --remote-name-all https://storage.googleapis.com/kubernetes-release/release/${RELEASE}/bin/linux/${ARCH}/{kubeadm,kubelet,kubectl}
   chmod +x {kubeadm,kubelet,kubectl} && cd
   mkdir -p /etc/systemd/system/kubelet.service.d

   echo "[TASK 9] create unit files for kubelet"
   cat >>/etc/systemd/system/kubelet.service<<EOF
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
   EOF
   cat >>/etc/systemd/system/kubelet.service.d/10-kubeadm.conf<<EOF
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
   ExecStart=/usr/local/bin/kubelet \$KUBELET_KUBECONFIG_ARGS \$KUBELET_CONFIG_ARGS \$KUBELET_KUBEADM_ARGS \$KUBELET_EXTRA_ARGS
   EOF

   echo "[TASK 10] enable and start kubelet service"
   systemctl enable kubelet >/dev/null 2>&1
   systemctl start kubelet

   echo "[TASK 11] enable root ssh password auth"
   sed -i 's/#PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
   sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
   systemctl reload sshd

   echo "[TASK 12] set root password"
   echo -e "P@ssw0rd\nP@ssw0rd" | passwd root >/dev/null 2>&1

.. code-block:: text
   :caption: bootstrap_kmaster.sh

   #!/bin/bash

   # Initialize Kubernetes
   echo "[TASK 13] initialize kubernetes cluster"
   kubeadm init --apiserver-advertise-address=192.168.2.100 --pod-network-cidr=192.168.0.0/16 # >> /root/kubeinit.log 2>/dev/null

   # copy kubeadm config
   echo "[TASK 14] copy kubeadm config to vagrant user .kube directory"
   mkdir /home/vagrant/.kube
   cp /etc/kubernetes/admin.conf /home/vagrant/.kube/config
   chown -R vagrant:vagrant /home/vagrant/.kube

   # deploy calico network
   echo "[TASK 15] deploy calico network"
   su - vagrant -c "kubectl create -f https://docs.projectcalico.org/v3.14/manifests/calico.yaml"

   # generate cluster join command
   echo "[TASK 16] Generate and save cluster join command to /joincluster.sh"
   kubeadm token create --print-join-command > /joincluster.sh

.. code-block:: text
   :caption: bootstrap_kworker.sh

   #!/bin/bash

   # join worker nodes to the cluster
   echo "[TASK 13] copy over cluster join script"
   sshpass -p "P@ssw0rd" scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no k8smaster001.lab.pwned.com:/joincluster.sh /joincluster.sh 2>/dev/null
   echo "[TASK 14] join this node to the cluster"
   bash /joincluster.sh >/dev/null 2>&1

Then run vagrant up
-------------------

.. code-block:: text

   $ vagrant up

Copy the config from the master locally
---------------------------------------

.. code-block:: text

   $ mkdir ~/.kube
   $ scp root@k8smaster001:/etc/kubernetes/admin.conf ~/.kube/config

The cluster should now be accessible
------------------------------------

.. code-block:: text

   $ kubectl get nodes
   NAME         STATUS  ROLES   AGE     VERSION
   k8smaster001 Ready   master  5m39s   v1.18.4
   k8sworker001 Ready   <none>  3m35s   v1.18.4
   k8sworker002 Ready   <none>  104s    v1.18.4

To tear down the cluster
------------------------

.. code-block:: text

   $ vagrant destroy
