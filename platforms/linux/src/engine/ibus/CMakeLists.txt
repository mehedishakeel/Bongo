include_directories(../riti/include ../../shared ${IBUS_INCLUDE_DIRS})
add_executable(ibus-bongo main.cpp)
target_link_libraries(ibus-bongo riti libShared Qt5::Core ${IBUS_LIBRARIES} dl pthread)

## Configure the files
configure_file(${CMAKE_SOURCE_DIR}/data/bongo.xml.in ${CMAKE_BINARY_DIR}/data/bongo.xml)
configure_file(${CMAKE_SOURCE_DIR}/data/bongo.desktop.in ${CMAKE_BINARY_DIR}/data/bongo.desktop)

## Install things
install(FILES ${CMAKE_SOURCE_DIR}/data/32.png
        DESTINATION ${PROJECT_DATADIR}/icons
        RENAME Bongo.png)

install(FILES ${CMAKE_SOURCE_DIR}/data/1024.png
        DESTINATION ${DATADIR}/pixmaps/
        RENAME bongo.png)

install(FILES ${CMAKE_SOURCE_DIR}/data/16.png
        DESTINATION ${DATADIR}/icons/hicolor/16x16/apps/
        RENAME bongo.png)

install(FILES ${CMAKE_SOURCE_DIR}/data/32.png
        DESTINATION ${DATADIR}/icons/hicolor/32x32/apps/
        RENAME bongo.png)

install(FILES ${CMAKE_SOURCE_DIR}/data/48.png
        DESTINATION ${DATADIR}/icons/hicolor/48x48/apps/
        RENAME bongo.png)

install(FILES ${CMAKE_SOURCE_DIR}/data/128.png
        DESTINATION ${DATADIR}/icons/hicolor/128x128/apps/
        RENAME bongo.png)

install(FILES ${CMAKE_SOURCE_DIR}/data/512.png
        DESTINATION ${DATADIR}/icons/hicolor/512x512/apps/
        RENAME bongo.png)

install(FILES ${CMAKE_SOURCE_DIR}/data/1024.png
        DESTINATION ${DATADIR}/icons/hicolor/1024x1024/apps/
        RENAME bongo.png)

install(FILES ${CMAKE_SOURCE_DIR}/data/avrophonetic.json
        DESTINATION ${PROJECT_DATADIR}/layouts)

install(FILES ${CMAKE_SOURCE_DIR}/data/Borno.json
        DESTINATION ${PROJECT_DATADIR}/layouts)

install(FILES ${CMAKE_SOURCE_DIR}/data/Avro_Easy.json
        DESTINATION ${PROJECT_DATADIR}/layouts)

install(FILES ${CMAKE_SOURCE_DIR}/data/Munir_Optima.json
        DESTINATION ${PROJECT_DATADIR}/layouts)

install(FILES ${CMAKE_SOURCE_DIR}/data/National_Jatiya.json
        DESTINATION ${PROJECT_DATADIR}/layouts)

install(FILES ${CMAKE_SOURCE_DIR}/data/Probhat.json
        DESTINATION ${PROJECT_DATADIR}/layouts)

install(FILES ${CMAKE_SOURCE_DIR}/data/autocorrect.json
        DESTINATION ${PROJECT_DATADIR}/data)

install(FILES ${CMAKE_SOURCE_DIR}/data/dictionary.json
        DESTINATION ${PROJECT_DATADIR}/data)

install(FILES ${CMAKE_SOURCE_DIR}/data/suffix.json
        DESTINATION ${PROJECT_DATADIR}/data)

install(FILES ${CMAKE_SOURCE_DIR}/data/regex.json
        DESTINATION ${PROJECT_DATADIR}/data)

install(FILES ${CMAKE_BINARY_DIR}/data/bongo.xml
        DESTINATION "${DATADIR}/ibus/component")

install(FILES ${CMAKE_BINARY_DIR}/data/bongo.desktop
        DESTINATION "${DATADIR}/applications")

install(FILES ${CMAKE_SOURCE_DIR}/data/org.bongo.keyboard.metainfo.xml
        DESTINATION ${DATADIR}/metainfo)

install(TARGETS ibus-bongo
        RUNTIME DESTINATION ${PROJECT_DATADIR})
