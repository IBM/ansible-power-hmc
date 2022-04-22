.. ...........................................................................
.. © Copyright IBM Corporation 2020                                          .
.. ...........................................................................

Installation
============

You can install the **IBM Power Systems HMC collection** using one of these options:
Ansible Galaxy or a local build.

For more information on installing collections, see `using collections`_.

.. _using collections:
   https://docs.ansible.com/ansible/latest/user_guide/collections_using.html

Ansible Galaxy
--------------
Galaxy enables you to quickly configure your automation project with content
from the Ansible community.

Galaxy provides prepackaged units of work known as collections. You can use the
`ansible-galaxy`_ command with the option ``install`` to install a collection on
your system (control node) hosted in Galaxy.

By default, the `ansible-galaxy`_ command installs the latest available
collection, but you can add a version identifier to install a specific version.
Before installing a collection from Galaxy, review all the available versions.
Periodically, new releases containing enhancements and features you might be
interested in become available.

The ansible-galaxy command ignores any pre-release versions unless
the ``==`` range identifier is set to that pre-release version.
A pre-release version is denoted by appending a hyphen and a series of
dot separated identifiers immediately following the patch version. The
**IBM Power Systems HMC collection** releases collections with the pre-release
naming convention such as **1.0.0-beta1** that would require a range identifier.

Here is an example of installing a pre-release collection:

.. code-block:: sh

   $ ansible-galaxy collection install ibm.power_hmc:==1.0.0-beta1


If you have installed a prior version, you must overwrite an existing
collection with the ``--force`` option.

Here are a few examples of installing the **IBM Power Systems HMC collection**:

.. code-block:: sh

   $ ansible-galaxy collection install ibm.power_hmc
   $ ansible-galaxy collection install -f ibm.power_hmc
   $ ansible-galaxy collection install --force ibm.power_hmc

The collection installation progress will be output to the console. Note the
location of the installation so that you can review other content included with
the collection, such as the sample playbook. By default, collections are
installed in ``~/.ansible/collections``; see the sample output.

.. _ansible-galaxy:
   https://docs.ansible.com/ansible/latest/cli/ansible-galaxy.html

.. code-block:: sh

   Process install dependency map
   Starting collection install process
   Installing 'ibm.power_hmc:1.0.0' to '/Users/user/.ansible/collections/ansible_collections/ibm/power_hmc'

After installation, the collection content will resemble this hierarchy: :

.. code-block:: sh

   ├── collections/
   │  ├── ansible_collections/
   │      ├── ibm/
   │          ├── power_hmc/
   │              ├── docs/
   │              ├── playbooks/
   │              ├── plugins/
   │                  ├── module_utils/
   │                  ├── modules/


You can use the `-p` option with `ansible-galaxy` to specify the installation
path, such as:

.. code-block:: sh

   $ ansible-galaxy collection install ibm.power_hmc -p /home/ansible/collections

When using the `-p` option to specify the install path, use one of the values
configured in COLLECTIONS_PATHS, as this is where Ansible itself will expect
to find collections.

For more information on installing collections with Ansible Galaxy,
see `installing collections`_.

.. _installing collections:
   https://docs.ansible.com/ansible/latest/user_guide/collections_using.html#installing-collections-with-ansible-galaxy


Local build
-----------

You can use the ``ansible-galaxy collection install`` command to install a
collection built from source. Version builds are available in the ``builds``
directory of the IBM ansible-power-hmc Git repository. The archives can be
installed locally without having to Galaxy.

To install a build from the ansible-power-hmc Git repository:

   1. Obtain a local copy from the Git repository:

      .. note::
         * Collection archive names will change depending on the release version.
         * They adhere to this convention **<namespace>-<collection>-<version>.tar.gz**, for example, **ibm-power_hmc-1.0.0.tar.gz**


   2. Install the local collection archive:

      .. code-block:: sh

         $ ansible-galaxy collection install ibm-power_hmc-1.0.0.tar.gz

      In the output of collection installation, note the installation path to access the sample playbook:

      .. code-block:: sh

         Process install dependency map
         Starting collection install process
         Installing 'ibm.power_hmc:1.0.0' to '/Users/user/.ansible/collections/ansible_collections/ibm/power_hmc'

      You can use the ``-p`` option with ``ansible-galaxy`` to specify the
      installation path, for example, ``ansible-galaxy collection install ibm-power_hmc-1.0.0.tar.gz -p /home/ansible/collections``.

      For more information, see `installing collections with Ansible Galaxy`_.

      .. _installing collections with Ansible Galaxy:
         https://docs.ansible.com/ansible/latest/user_guide/collections_using.html#installing-collections-with-ansible-galaxy
 

Build Execution Environment Image
---------------------------------
By default, the published execution environment images unlikely to contain the HMC collections. For that user may need to create custom ee image to package
the HMC collection along with base universal ee image.

Following step demonstrate how an ansible execution environment image can be created to support Ansible Automation Platform 2.X based environment:

   1. Setup the machine with ansible builder tool. Refer `official documentation`_

   .. _official documentation:
      https://ansible-builder.readthedocs.io/en/latest/

   2. Build the ee image using the `execution environment configuration yaml`_. Make sure the command is executed from the home path where yaml file is present.

      .. _execution environment configuration yaml:
         https://github.com/IBM/ansible-power-hmc/blob/dev-collection/execution-environment.yml

      .. code-block:: sh

         $ansible-builder build –t <image_tag>
