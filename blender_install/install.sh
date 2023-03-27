#!/bin/bash
# Status codes:
# 0 - everything is ok
# 1 - blender python script failed
# 2 - archive unpacking is not successful

# Get data from git
echo -e 'Install script:\n- pulls binaries from LFS\n'\
'- unpacks portable version of Blender3D\n'\
'- installs components for correct operation\n- installs Pip locally\n'\
'- pulls Python dependencies\n- activates addons\n'
echo 'Pulling binaries'
printf $GIT_PASS\n | git pull && git lfs pull
echo -e '\nChecking portable installation'

# Remember the original folder from which script started
opwd=`pwd`
status=1
cd .. && cd blender_portable && \
sha512sum -c --status ../blender_portable.sha512; status=$?

if [ $status == 0 ]; then
  echo 'Blender installation is ok, nothing will be changed'
  cd $opwd
else
  echo '"blender_portable" folder is not found or installation is broken'
  echo 'Reinstalling portable Blender'
  echo 'Checking the portable archive sha512'
  cd $opwd/../binaries && echo `pwd`
  sha512sum -c --status blender-portable-linux-x64.sha512; status=$?

  # Execute unpacking and installation if check is successfull
  if [ $status == 0 ]; then
    echo 'Portable Blender archive is ok, unpacking and installing'
    cd .. && echo 'Unpacking portable Blender installation'
    rm -rf ./blender_portable && mkdir ./blender_portable
    tar -xf ./binaries/blender-portable-linux-x64.tar.xz \
    -C ./blender_portable --strip-components=1; status=$?; cd $opwd

    if [ $status == 0 ]; then
      echo -e '\nUnpacking finished'
    else
      echo -e '\nUnable to unpack'
      exit 2
    fi

  else
    echo "Portable Blender archive checksum doesn't match"
    exit 2
  fi
fi


echo 'Making blender config folder if not present'
mkdir -p ~/.config/blender
cd $opwd && \
python install.py -c install_config.yaml
status=$?

if [ $status == 0 ]; then
  echo -e '\nInstallation finished successfully'
else
  echo -e '\nInstallation failed, see logs'
fi

exit $status
