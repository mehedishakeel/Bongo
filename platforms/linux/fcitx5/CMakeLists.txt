cmake_minimum_required(VERSION 3.16)
project(bongo-fcitx5 VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(REQUIRED_FCITX_VERSION 5.1.0)

find_package(Fcitx5Core ${REQUIRED_FCITX_VERSION} REQUIRED)

include(GNUInstallDirs)
include(CTest)

add_fcitx5_addon(bongo
    src/bongo.cpp
    src/bongo_state.cpp
    src/bongo_settings.cpp
    src/bongo_api.cpp
    src/bongo_keymap.cpp
)
target_include_directories(bongo PRIVATE src)
target_link_libraries(bongo PRIVATE Fcitx5::Core ${CMAKE_DL_LIBS})

install(TARGETS bongo DESTINATION "${FCITX_INSTALL_ADDONDIR}")

configure_file(data/bongo-addon.conf.in
               "${CMAKE_CURRENT_BINARY_DIR}/bongo-addon.conf" @ONLY)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/bongo-addon.conf"
        DESTINATION "${FCITX_INSTALL_PKGDATADIR}/addon"
        RENAME bongo.conf)
install(FILES data/bongo.im.conf
        DESTINATION "${FCITX_INSTALL_PKGDATADIR}/inputmethod"
        RENAME bongo.conf)

if(BUILD_TESTING)
    file(MAKE_DIRECTORY
        "${CMAKE_BINARY_DIR}/testdata/addon"
        "${CMAKE_BINARY_DIR}/testdata/inputmethod"
    )
    configure_file(data/bongo-addon.conf.in
        "${CMAKE_BINARY_DIR}/testdata/addon/bongo.conf" @ONLY)
    configure_file(data/bongo.im.conf
        "${CMAKE_BINARY_DIR}/testdata/inputmethod/bongo.conf" COPYONLY)
    configure_file(tests/testfrontend.conf
        "${CMAKE_BINARY_DIR}/testdata/addon/testfrontend.conf" COPYONLY)

    add_executable(bongo-settings-test
        tests/test_settings.cpp
        src/bongo_settings.cpp
    )
    target_include_directories(bongo-settings-test PRIVATE src)
    target_compile_features(bongo-settings-test PRIVATE cxx_std_20)
    add_test(NAME bongo-settings COMMAND bongo-settings-test)

    add_executable(bongo-engine-api-test
        tests/test_engine_api.cpp
        src/bongo_api.cpp
    )
    target_include_directories(bongo-engine-api-test PRIVATE src)
    target_compile_features(bongo-engine-api-test PRIVATE cxx_std_20)
    target_link_libraries(bongo-engine-api-test PRIVATE Fcitx5::Core ${CMAKE_DL_LIBS})
    add_test(NAME bongo-engine-api COMMAND bongo-engine-api-test)

    add_executable(bongo-keymap-test
        tests/test_keymap.cpp
        src/bongo_keymap.cpp
    )
    target_include_directories(bongo-keymap-test PRIVATE src)
    target_compile_features(bongo-keymap-test PRIVATE cxx_std_20)
    target_link_libraries(bongo-keymap-test PRIVATE Fcitx5::Core)
    add_test(NAME bongo-keymap COMMAND bongo-keymap-test)

    if(DEFINED ENV{BONGO_ENGINE_LIB} AND NOT BONGO_ENGINE_LIB)
        set(BONGO_ENGINE_LIB "$ENV{BONGO_ENGINE_LIB}")
    endif()
    if(BONGO_ENGINE_LIB)
        add_executable(bongo-fcitx5-integration-test
            tests/test_fcitx5_integration.cpp
        )
        target_include_directories(bongo-fcitx5-integration-test PRIVATE tests)
        target_compile_features(bongo-fcitx5-integration-test PRIVATE cxx_std_20)
        target_link_libraries(bongo-fcitx5-integration-test PRIVATE Fcitx5::Core)
        add_test(NAME bongo-fcitx5-integration
            COMMAND ${CMAKE_COMMAND} -E env
                "FCITX_ADDON_DIRS=${CMAKE_BINARY_DIR}:/usr/lib/fcitx5:/usr/lib64/fcitx5:/usr/lib/x86_64-linux-gnu/fcitx5"
                "FCITX_DATA_HOME=${CMAKE_BINARY_DIR}/testdata"
                "XDG_CONFIG_HOME=${CMAKE_BINARY_DIR}/testconfig"
                "BONGO_ENGINE_LIB=${BONGO_ENGINE_LIB}"
                $<TARGET_FILE:bongo-fcitx5-integration-test>
        )
    endif()
endif()
