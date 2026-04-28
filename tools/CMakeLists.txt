# Add cmake commands: rp6502_executable() and rp6502_asset()
cmake_minimum_required(VERSION 3.17)

# Package the target as an RP6502 ROM.
#
# RP6502 Executable ROM
# ^^^^^^^^^^^^^^^^^^^^^
#
#  rp6502_executable(<name>
#                    [DATA <addr>]
#                    [NMI <addr>]
#                    [RESET <addr>]
#                    [IRQ <addr>]
#                    roms...)
#
# Packages the ``<name>`` into RP6502 ROM format. Merges with
# specified ``roms...`` and those created with rp6502_asset().
# The word `file` may be used for any <addr> indicating the
# address is to be read from the linker output in this order:
# ``DATA <addr>`` Starting memory address to load data.
# ``NMI <addr>`` Address for NMI to be stored at $FFFA-$FFFB.
# ``RESET <addr>`` Address for RESET to be stored at $FFFC-$FFFD.
# ``IRQ <addr>`` Address for IRQ to be stored at $FFFE-$FFFF.
#
function(rp6502_executable name)
    # Parse args
    set(data_addr "none")
    set(nmi_addr "none")
    set(reset_addr "none")
    set(irq_addr "none")
    set(extra_roms)
    foreach(X IN LISTS ARGN)
        if (NOT data_addr)
            set(data_addr ${X})
        elseif (NOT reset_addr)
            set(reset_addr ${X})
        elseif (NOT irq_addr)
            set(irq_addr ${X})
        elseif (NOT nmi_addr)
            set(nmi_addr ${X})
        elseif (X STREQUAL "DATA")
            set(data_addr FALSE)
        elseif (X STREQUAL "RESET")
            set(reset_addr FALSE)
        elseif (X STREQUAL "IRQ")
            set(irq_addr FALSE)
        elseif (X STREQUAL "NMI")
            set(nmi_addr FALSE)
        else ()
            list(APPEND extra_roms ${X})
        endif ()
    endforeach()
    # Resolve relative extra_roms against current source dir
    set(all_extra_roms)
    foreach(rom IN LISTS extra_roms)
        if (IS_ABSOLUTE "${rom}")
            list(APPEND all_extra_roms "${rom}")
        else()
            list(APPEND all_extra_roms "${CMAKE_CURRENT_SOURCE_DIR}/${rom}")
        endif()
    endforeach()
    # Collect asset ROMs registered by rp6502_asset()
    get_target_property(asset_roms ${name} RP6502_ASSET_ROMS)
    if (asset_roms)
        list(APPEND all_extra_roms ${asset_roms})
    endif()
    # Remove old ROM
    add_custom_command(TARGET ${name} PRE_BUILD
        COMMAND ${CMAKE_COMMAND} -E rm -f
        "${CMAKE_CURRENT_BINARY_DIR}/${name}.rp6502"
    )
    # Create new ROM
    find_package(Python3 REQUIRED COMPONENTS Interpreter)
    set(tool_command "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/tools/rp6502.py"
    )
    if (NOT data_addr STREQUAL "none")
        list(APPEND tool_command
            -a "${data_addr}"
        )
    else ()
        message (FATAL_ERROR "rp6502_executable DATA address missing")
    endif ()
    if (NOT nmi_addr STREQUAL "none")
        list(APPEND tool_command
            -n "${nmi_addr}"
        )
    endif ()
    if (NOT reset_addr STREQUAL "none")
        list(APPEND tool_command
            -r "${reset_addr}"
        )
    else ()
        message (FATAL_ERROR "rp6502_executable RESET address missing")
    endif ()
    if (NOT irq_addr STREQUAL "none")
        list(APPEND tool_command
            -i "${irq_addr}"
        )
    endif ()
    list(APPEND tool_command
        -o "${CMAKE_CURRENT_BINARY_DIR}/${name}.rp6502"
        create "${CMAKE_CURRENT_BINARY_DIR}/${name}"
        -- ${all_extra_roms}
    )
    add_custom_command(TARGET ${name} POST_BUILD
        COMMAND ${tool_command}
    )
    set_property(TARGET ${name} APPEND PROPERTY
        LINK_DEPENDS ${all_extra_roms}
    )
    # Mark that rp6502_executable has been called for this target
    set_property(TARGET ${name} PROPERTY RP6502_EXECUTABLE_CALLED TRUE)
endfunction()

# Package anything in RP6502 ROM.
#
# RP6502 Asset ROM
# ^^^^^^^^^^^^^^^^
#
#  rp6502_asset(<name> address in_file)
#
# If the address is numeric, the in_file will be loaded into
# RAM ($0-FFFF) or XRAM ($10000-1FFFF) when the ROM is loaded.
# Non-numeric addresses become filenames that can be opened
# with "ROM:filename" from a micro filesystem in the ROM.
#
function(rp6502_asset name addr in_file)
    # Check if rp6502_executable has already been called
    get_target_property(executable_called ${name} RP6502_EXECUTABLE_CALLED)
    if (executable_called)
        message(FATAL_ERROR 
            "rp6502_asset(${name} ...) must be registered BEFORE calling rp6502_executable()."
        )
    endif()
    get_filename_component(src_file "${in_file}" ABSOLUTE BASE_DIR "${CMAKE_CURRENT_SOURCE_DIR}")
    file(RELATIVE_PATH rel_path "${CMAKE_SOURCE_DIR}" "${src_file}")
    if (rel_path MATCHES "^\\.\\.")
        get_filename_component(rel_path "${src_file}" NAME)
    endif()
    set(out_file "${CMAKE_CURRENT_BINARY_DIR}/CMakeFiles/${name}.rp6502/${rel_path}")
    find_package(Python3 REQUIRED COMPONENTS Interpreter)
    set(asset_command
        "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/tools/rp6502.py"
        -a "${addr}"
        -o "${out_file}"
        create "${src_file}"
    )
    get_filename_component(out_dir "${out_file}" DIRECTORY)
    add_custom_command(
        OUTPUT "${out_file}"
        DEPENDS "${src_file}"
        COMMAND ${CMAKE_COMMAND} -E make_directory "${out_dir}"
        COMMAND ${asset_command}
    )
    target_sources(${name} PRIVATE "${out_file}")
    set_property(TARGET ${name} APPEND PROPERTY
        RP6502_ASSET_ROMS "${out_file}"
    )
endfunction()
