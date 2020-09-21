.. ...........................................................................
.. © Copyright IBM Corporation 2020                                          .
.. ...........................................................................

Playbooks
=========

The sample playbooks that are **included** in the **IBM Power Systems HMC collection**
demonstrate how to use the collection content.

Playbook Documentation
----------------------

An `Ansible playbook`_ consists of organized instructions that define work for
a managed node (host) to be managed with Ansible.

A `playbooks directory`_ that contains a sample playbook is included in the
**IBM Power Systems HMC collection**. The sample playbook can be run with the
``ansible-playbook`` command with some modification to the **inventory**.

You can find the playbook content that is included with the collection in the
same location where the collection is installed. For more information, refer to
the `installation documentation`_. In the following examples, this document will
refer to the installation path as ``~/.ansible/collections/ansible_collections/ibm/power_hmc``.

.. _Ansible playbook:
   https://docs.ansible.com/ansible/latest/user_guide/playbooks_intro.html#playbooks-intro
.. _playbooks directory:
   https://github.com/IBM/ansible-power-hmc/tree/dev-collection/playbooks
.. _installation documentation:
   installation.html


Sample Configuration and Setup
------------------------------
Each release of Ansible provides options in addition to the ones identified in
the sample configurations that are included with this collection. These options
allow you to customize how Ansible operates in your environment. Ansible
supports several sources to configure its behavior and all sources follow the
Ansible `precedence rules`_.

The Ansible configuration file `ansible.cfg` can override almost all
``ansible-playbook`` configurations.

You can specify the SSH port used by Ansible and instruct Ansible where to
write the temporary files on the target. This can be easily done by adding the
options to your inventory or `ansible.cfg`.

For more information about available configurations for ``ansible.cfg``, read
the Ansible documentation on `Ansible configuration settings`_.


.. _precedence rules:
   https://docs.ansible.com/ansible/latest/reference_appendices/general_precedence.html#general-precedence-rules
.. _Ansible configuration settings:
   https://docs.ansible.com/ansible/latest/reference_appendices/config.html#ansible-configuration-settings-locations

Inventory
---------

Ansible works with multiple managed nodes (hosts) at the same time, using a
list or group of lists known as an `inventory`_. Once the inventory is defined,
you can use `patterns`_ to select the hosts or groups that you want Ansible to
run against.But the HMC collection will take a deviation from this standard 
expectation of Ansible inventory. Since HMC is a closed appliance application,
its restricted shell wont allow push based mode of Ansible. Hence all the 
communication will be happening from the control machine (node) itself
to the managed host (HMC).

To handle above limitation, always use connection plugin inside playbook and
provide it with the value **local** to execute tasks on the Ansible control node
instead of on a remote host

Included in the `playbooks directory`_ is a `sample inventory file`_ that can be
used to manage your nodes with a little modification. This inventory file
should be included when running the sample playbook.

.. code-block:: ini

   [hmcs]
   hmc01
   hmc02

   [hmcs:vars]
   ansible_user=hscroot


Inside the playbook, refer the mentioned  managed nodes (HMCs) from the inventory file
using the magic variable **inventory_hostname**

.. _inventory:
   https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html
.. _patterns:
   https://docs.ansible.com/ansible/latest/user_guide/intro_patterns.html#intro-patterns
.. _sample inventory file:
   https://github.com/IBM/ansible-power-hmc/tree/dev-collection/playbooks/inventory



Run the playbooks
-----------------

The sample playbooks must be run from the `playbooks directory`_ of the installed
collection: ``~/.ansible/collections/ansible_collections/ibm/power_hmc/playbooks/``.

Access the sample Ansible playbook and ensure that you are within the collection
playbooks directory where the sample files are included:
``~/.ansible/collections/ansible_collections/ibm/power_hmc/playbooks/``.

Use the Ansible command ``ansible-playbook`` to run the sample playbooks.  The
command syntax is ``ansible-playbook -i <inventory> <playbook>``; for example,
``ansible-playbook -i inventory demo_hmc_update.yml``.

HMC Password Settings
"""""""""""""""""""""
Either mention the password of managed node (HMC) on the playbook as a variable,
but never store this variable in plain text; always use a vault. Or user can setup
the password less login to HMC using the ``mkauthkey`` with the public SSH key of
control node, for example ``mkauthkeys -a <public_key>``. Sample playbook is included
which takes care of passwordless setup on managed HMCs:
``~/.ansible/collections/ansible_collections/ibm/power_hmc/playbooks/demo_passwordless_setup.yml``

Verbosity 
"""""""""
Optionally, you can configure the console logging verbosity during playbook
execution. This is helpful in situations where communication is failing and
you want to obtain more details. To adjust the logging verbosity, append more
letter `v`'s; for example, `-v`, `-vv`, `-vvv`, or `-vvvv`.

Each letter `v` increases logging verbosity similar to traditional logging
levels INFO, WARN, ERROR, DEBUG.

.. note::
   It is a good practice to review the playbook samples before executing them.
   It will help you understand what requirements in terms of space, location,
   names, authority, and artifacts will be created and cleaned up. Although
   samples are always written to operate without the need for the user's
   configuration, flexibility is written into the samples because it is not
   easy to determine if a sample has access to the host's resources.
   Review the playbook notes sections for additional details and
   configuration.

.. _playbooks directory:
   https://github.com/IBM/ansible-power-hmc/tree/dev-collection/playbooks

.. _mkauthkey documentation:
   https://www.ibm.com/support/knowledgecenter/POWER9/p9edm/mkauthkeys.html

