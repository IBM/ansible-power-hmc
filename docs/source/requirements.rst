.. ...........................................................................
.. © Copyright IBM Corporation 2020                                          .
.. ...........................................................................

Requirements
============

A control node is any machine with Ansible installed. From the control node,
you can run commands and playbooks from a laptop, desktop, or server.
However, you cannot run **IBM Power Systems HMC collection** on a Windows system.

A managed node is often referred to as a target node, or host, and it is managed
by Ansible. Ansible is not required on a managed node.

The nodes listed below require these specific versions of software:

Control node
------------

* `Ansible version`_: 2.9 or later
* `Python`_: 3

.. _Ansible version:
   https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html
.. _Python:
   https://www.python.org/downloads/release/latest


Managed node
------------


