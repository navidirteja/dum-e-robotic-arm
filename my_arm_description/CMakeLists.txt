cmake_minimum_required(VERSION 3.8)
project(my_arm_description)

find_package(ament_cmake REQUIRED)

# This package contains only data files. Installing them into
# install/my_arm_description/share/my_arm_description/ is what lets launch
# files and package:// URIs find them after `colcon build`.
install(
  DIRECTORY urdf launch rviz
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
