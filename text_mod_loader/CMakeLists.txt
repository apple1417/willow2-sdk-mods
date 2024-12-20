file(GLOB_RECURSE sources CONFIGURE_DEPENDS "file_parser/*.cpp" "file_parser/*.h")

if(NOT DEFINED TML_FILE_PARSER_NATIVE_LINUX)
# By default, assume we're imported from the repo root, use pyunrealsdk to build

    pyunrealsdk_add_module(tml_file_parser ${sources})

    # Slight hack: we don't actually rely on pyunrealsdk, but using it's helper function sets up
    # everything for us, so just redefine the link libraries here to not rely on it
    set_property(TARGET tml_file_parser PROPERTY LINK_LIBRARIES)
    target_link_libraries(tml_file_parser PRIVATE explicit_python pybind11::module)

else()
# If `TML_FILE_PARSER_NATIVE_LINUX` is defined, instead treat this as a brand new cmake project
# This can be used to compile this as a native linux module - useful for tests or debugging on a
# linux host

    cmake_minimum_required(VERSION 3.24)
    project(tml_file_parser)

    add_subdirectory(../.libs/pugixml subproject/pugixml EXCLUDE_FROM_ALL)
    add_subdirectory(../.willow2-mod-manager/libs/pyunrealsdk/libs/pybind11 subproject/pybind11 EXCLUDE_FROM_ALL)

    pybind11_add_module(tml_file_parser ${sources})

    target_compile_features(tml_file_parser PUBLIC cxx_std_20)
    set_target_properties(tml_file_parser PROPERTIES
        COMPILE_WARNING_AS_ERROR True
        INTERPROCEDURAL_OPTIMIZATION True
        EXPORT_COMPILE_COMMANDS True
        PREFIX ""
    )

    target_compile_definitions(tml_file_parser PUBLIC PYBIND11_DETAILED_ERROR_MESSAGES=1)

endif()

set_property(TARGET tml_file_parser PROPERTY OUTPUT_NAME "file_parser")
target_link_libraries(tml_file_parser PRIVATE pugixml)

install(
    TARGETS
        tml_file_parser
    DESTINATION
        ${CMAKE_CURRENT_SOURCE_DIR}
)
