#include "catch/catch.hpp"
#include "enums.h"
#include "tileray.h"

#include <vector>

#define RUNCHECK 1

#ifdef PRINTOUT
#include <stdio.h>
#endif

TEST_CASE( "test_tilerays" )
{
    tileray tray;
    tileray fray;
    for( int angle = 0; angle < 360; angle += 1 ) {
        tray.init( angle );
        fray.init( angle );
        for( int overall = 1; overall < 122; overall += 1 ) {
            for( int step_size = 1; step_size <= overall; step_size += 1 ) {
                tray.clear_advance();
                fray.clear_advance();
                for( int i = step_size; i <= overall; i += step_size ) {
                    tray.slow_advance( step_size );
                    fray.advance( step_size );
                }
#ifdef RUNCHECK
                CHECK( tray.dx() == fray.dx() );
                CHECK( tray.dy() == fray.dy() );
                CHECK( std::abs( fray.dx() ) <= step_size );
                CHECK( std::abs( fray.dx() ) >= 0 );
                CHECK( std::abs( fray.dy() ) <= step_size );
                CHECK( std::abs( fray.dy() ) >= 0 );
#endif
#if 0
                if( std::abs( fray.dy() ) > step_size || tray.dx() != fray.dx() || tray.dy() != tray.dy() ) {
                    printf("angle %d, overall %d, step %d, tray %d:%d, fray %d:%d\n",
                            angle, overall, step_size, tray.dx(), tray.dy(),
                            fray.dx(), fray.dy() ); 
                }
#endif
                tray.clear_advance();
                fray.clear_advance();
                for( int i = step_size; i <= overall; i += step_size ) {
                    tray.slow_advance( -step_size );
                    fray.advance( -step_size );
                }
#ifdef RUNCHECK
                CHECK( tray.dx() == fray.dx() );
                CHECK( tray.dy() == fray.dy() );
                CHECK( std::abs( fray.dx() ) <= step_size );
                CHECK( std::abs( fray.dx() ) >= 0 );
                CHECK( std::abs( fray.dy() ) <= step_size );
                CHECK( std::abs( fray.dy() ) >= 0 );
#endif
            }
        }
    }
}
