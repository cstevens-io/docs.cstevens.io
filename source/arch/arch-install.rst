##################
Arch Linux install
##################

.. attention:: Please refer to the `Arch Wiki <https://wiki.archlinux.org>`_ for the official guide on how to install Arch Linux.

Setup disk partitions
=====================

.. code-block:: text
   
    # parted /dev/sda
    (parted) mklabel gpt
    (parted) mkpart primary fat32 1MiB 512MiB
    (parted) set 1 esp on
    (parted) mkpart primary linux-swap 512MiB 2560MiB
    (parted) mkpart primary ext4 2560MiB 100%
    (parted) quit

Format partitions
=================

.. code-block:: text

    # mkfs.fat -F32 /dev/sda1
    # mkswap /dev/sda2
    # mkfs.ext4 /dev/sda3

Mount partitions
================

.. code-block:: text

    # mount /dev/sda3 /mnt
    # mkdir /mnt/boot
    # mount /dev/sda1 /mnt/boot
    # swapon /dev/sda2

Install the base system and enter chroot
========================================

.. code-block:: text

    # pacstrap /mnt base linux vim
    # genfstab -U /mnt >> /mnt/etc/fstab
    # arch-chroot /mnt

Set local timezone and create /etc/adjtime
==========================================

.. code-block:: text

    # ln -sf /usr/share/zoneinfo/America/Los_Angeles /etc/localtime
    # hwclock --systohc

Set and generate locale
=======================

.. code-block:: text

    # echo "en_US.UTF-8 UTF-8" > /etc/locale.gen
    # locale-gen
    # echo "LANG=en_US.UTF-8" > /etc/locale.conf

Set the host name
=================

.. code-block:: text

    # hostnamectl set-hostname <hostname>

Adjust the hosts file
=====================

.. code-block:: text
    :caption: /etc/hosts

    127.0.0.1    localhost.localdomain   localhost
    ::1          localhost6.localdomain   localhost6
    192.168.1.250 $myhostname.$mydomain   $myhostname
    2001:470:8050:1::250 $myhostname.$mydomain  $myhostname

Enable NTP daemon
=================

.. code-block:: text

    # timedatectl set-ntp true

Set the root password
=====================

.. code-block:: text

    # passwd
   
Create files for and install systemd-boot 
=========================================

.. code-block:: text

    # mkdir -p /boot/loader/entries

.. code-block:: text
    :caption: /boot/loader/loader.conf

    default arch
    console-mode max
    timeout 5

.. code-block:: text
    :caption: /boot/loader/entries/arch.conf

    title Arch Linux
    linux /vmlinuz-linux
    initrd /initramfs-linux.img
    options root=/dev/sda3 net.ifnames=0

Install systemd-boot:

.. code-block:: text

    # bootctl --path=/boot install

Configure networking
====================

DHCP
----

.. code-block:: text
    :caption: /etc/systemd/network/eth0.network

    [Match]
    Name=eth0

    [Network]
    DHCP=yes

Static
------

.. code-block:: text
    :caption: /etc/systemd/network/eth0.network

    [Match]
    Name=eth0

    [Network]
    Address=192.168.1.250/24
    Gateway=192.168.1.1
    DNS=192.168.1.53

    Address=2001:470:8050:1::250/64
    Gateway=2001:470:8050:1::1
    DNS=2001:470:8050:1::53

Enable networking on boot

.. code-block:: text

    # systemctl enable systemd-networkd
    # systemctl enable systemd-resolved

Exit chroot and reboot
======================

.. code-block:: text

    # exit
    # reboot
