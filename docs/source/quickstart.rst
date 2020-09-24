.. ...........................................................................
.. © Copyright IBM Corporation 2020                                          .
.. ...........................................................................

Quickstart
==========

After installing the collection outlined in the  `installation`_ guide, you
can access the collection and the ansible-doc covered in the following topics:

.. _installation:
   installation.html

ibm.power_hmc
--------------

After the collection is installed, you can access the collection content for a
playbook by referencing the namespace ``ibm`` and the collection's fully
qualified name ``power_hmc``. For example:

.. code-block:: yaml

    - hosts: all

    tasks:
    - name: Query HMC current build level
      ibm.power_hmc.hmc_build_manager:
          state: facts
          hmc_host: '{{ inventory_hostname }}'
          hmc_auth:
              userid: '{{ ansible_user }}'


In Ansible 2.9, the ``collections`` keyword was added to reduce the need
to refer to the collection repeatedly. For example, you can use the
``collections`` keyword in your playbook:

.. code-block:: yaml

    - hosts: all
      collections:
      - ibm.power_hmc

    tasks:
    - name: Query HMC current build level
      hmc_build_manager:
          state: facts
          hmc_host: '{{ inventory_hostname }}'
          hmc_auth:
              userid: '{{ ansible_user }}'

ansible-doc
-----------

Modules included in this collection provide additional documentation that is
similar to a UNIX-like operating system man page (manual page). This
documentation can be accessed from the command line by using the
``ansible-doc`` command.

Here's how to use the ``ansible-doc`` command after you install the
**IBM Power Systems HMC collection**: ``ansible-doc ibm.power_hmc.hmc_build_manager``

.. code-block:: sh

     > HMC_BUILD_MANAGER    (ansible_collections/ibm/power_hmc/plugins/modules/hmc_build_manager.py)

        Updates the HMC by installing a corrective service package located on an FTP/SFTP/NFS server or HMC hard disk Or
        Upgrades the HMC by obtaining  the required  files  from a remote server or from the HMC hard disk. The files are
        transferred onto a special partition on the HMC hard disk. After the files have been transferred, HMC will boot from
        this partition and perform the upgrade


For more information on using the ``ansible-doc`` command, refer
to the `Ansible guide`_.

.. _Ansible guide:
   https://docs.ansible.com/ansible/latest/cli/ansible-doc.html#ansible-doc

Connection Method
-----------------

Ansible communicates with remote machines over the SSH protocol. By default, Ansible uses native OpenSSH and connects to remote machines and communicates from the control node via SSH tunnel.

In case of HMC collection, since HMC is a closed appliance solution, its restricted shell will not allow push-based execution model of Ansible. Hence , current ansible collection for HMC would work with local connection type using the connection plugin, executing commands via SSH without pushing the code to the managed HMC. 

