cmake_minimum_required(VERSION 3.24)

project(willow2_sdk_mods)

add_subdirectory(.willow2-mod-manager EXCLUDE_FROM_ALL)
set_target_properties(pluginloader_no_proxy PROPERTIES EXCLUDE_FROM_ALL true)

add_subdirectory(.libs/pugixml EXCLUDE_FROM_ALL)

# If using the clang windows cross compilation toolchain
if((NOT CMAKE_HOST_WIN32)
    AND (CMAKE_SYSTEM_NAME STREQUAL "Windows")
    AND (CMAKE_CXX_COMPILER_ID STREQUAL "Clang"))
    # HACK: We normally use -idirafter to make clang forwards msvc's intrinsics properly. Something
    #       about doing this causes _isnan to not be defined, which pugixml depends on.
    #       Swap back to -isystem and it just works somehow?
    get_target_property(pugi_compile_options pugixml-static COMPILE_OPTIONS)
    string(REPLACE "-idirafter" "-isystem" pugi_compile_options "${pugi_compile_options}")
    set_target_properties(pugixml-static PROPERTIES COMPILE_OPTIONS "${pugi_compile_options}")
endif()

file(GLOB_RECURSE subfolders RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" "*/CMakeLists.txt")
foreach(cmakelists ${subfolders})
    if (${cmakelists} MATCHES "^\\.")
        continue()
    endif()

    get_filename_component(folder "${cmakelists}" DIRECTORY)
    message(STATUS "Including mod folder: ${folder}")
    add_subdirectory(${folder})
endforeach()
