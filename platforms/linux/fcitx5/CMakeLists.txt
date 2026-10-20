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
