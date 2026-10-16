/** 
* @file
* @brief  Cross platform wrapper to create a sleep function with millisecond precision.
*/

#ifndef MSSLEEP_H
#define MSSLEEP_H

#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#endif

#if defined(__MINGW32__) && !defined(__MINGW64_VERSION_MAJOR)
#include <winbase.h>
#elif defined(_WIN32)
#include <synchapi.h>
#else /* Assuming recent posix*/
#ifndef __USE_POSIX199309
#define __USE_POSIX199309 1
#endif
#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 199309L
#endif
#include <time.h>
#endif

/**
 * Yield the current thread for at least us microseconds.
 */
static inline void us_sleep(unsigned us)
{
#if defined(__EMSCRIPTEN__)
    emscripten_sleep((us + 999) / 1000);
#elif defined(_WIN32)
    Sleep((us + 999) / 1000);
#else
    struct timespec ts;
    ts.tv_sec = us / 1000000;
    ts.tv_nsec = (us % 1000000) * 1000;
    nanosleep(&ts, NULL);
#endif
}

/**
 * Yield the current thread for at least ms milliseconds.
 */
static inline void ms_sleep(unsigned ms)
{
#if defined(__EMSCRIPTEN__)
    emscripten_sleep(ms);
#elif defined(_WIN32)
    Sleep(ms);
#else
    struct timespec ts;
    ts.tv_sec = ms / 1000;
    ts.tv_nsec = (ms % 1000) * 1000000;
    nanosleep(&ts, NULL);
#endif
}

#ifdef __EMSCRIPTEN__
/**
 * Give the browser a turn (rendering, input, audio) if the game has not slept
 * for a while. Called from places that busy loops keep calling (input pump,
 * tick count), so loops written for DOS/Windows do not freeze the page.
 */
static inline void Web_Yield()
{
    static double last = 0;
    double now = emscripten_get_now();
    if (now - last >= 15) {
        emscripten_sleep(0);
        last = emscripten_get_now();
    }
}
#else
static inline void Web_Yield()
{
}
#endif

#endif /* MSSLEEP_H */
