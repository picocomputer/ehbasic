# Filter out arguments that should only go to IntelliSense.
# Errors and warnings adjusted for standard problem matcher.

# Args 0-3 are the cmake call to this script.
if(NOT CMAKE_ARGV3 STREQUAL "--")
    message(FATAL_ERROR "No -- separator found in arguments")
endif()

# First argument after -- is CC65_COMPILER.
set(CC65_COMPILER "${CMAKE_ARGV4}")
if(NOT EXISTS "${CC65_COMPILER}")
    message(FATAL_ERROR "Could not find executable: ${CC65_COMPILER}")
endif()

# Remove -include and its argument.
set(FILTERED_ARGS "")
foreach(INDEX RANGE 5 ${CMAKE_ARGC})
    if(DEFINED CMAKE_ARGV${INDEX})
        set(ARG "${CMAKE_ARGV${INDEX}}")
        if(ARG STREQUAL "-D__fastcall__=")
            # skip
        elseif(ARG STREQUAL "-D__cdecl__=")
            # skip
        else()
            list(APPEND FILTERED_ARGS "${ARG}")
        endif()
    endif()
endforeach()

# Execute the real compiler with filtered arguments.
execute_process(
    COMMAND ${CC65_COMPILER} ${FILTERED_ARGS}
    OUTPUT_VARIABLE STDOUT_OUTPUT
    ERROR_VARIABLE STDERR_OUTPUT
    RESULT_VARIABLE EXIT_CODE
)

# Output stdout unchanged.
if(STDOUT_OUTPUT)
    message(STATUS "${STDOUT_OUTPUT}")
endif()

# Reformat stderr so VS Code problem matcher works. Yes, it's just the case.
if(STDERR_OUTPUT)
    string(REGEX REPLACE "(:[0-9]+:) Error:" "\\1 error:" STDERR_OUTPUT "${STDERR_OUTPUT}")
    string(REGEX REPLACE "(:[0-9]+:) Warning:" "\\1 warning:" STDERR_OUTPUT "${STDERR_OUTPUT}")
    message(NOTICE "${STDERR_OUTPUT}")
endif()

# Return a non-zero exit code.
if(NOT EXIT_CODE EQUAL 0)
    message(FATAL_ERROR "Compilation failed with exit code ${EXIT_CODE}")
endif()
