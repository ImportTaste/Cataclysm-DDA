#include "catch/catch.hpp"
#include "enums.h"
#include "tileray.h"

#include <stdio.h>

#include <vector>
#include <map>
#include <unordered_map>

void slow_coord_translate( tileray tdir, const point &pivot, const point &p, point &q )
{
    tdir.clear_advance();
    tdir.slow_advance( p.x - pivot.x );
    q.x = tdir.dx() + tdir.ortho_dx( p.y - pivot.y );
    q.y = tdir.dy() + tdir.ortho_dy( p.y - pivot.y );
}

void coord_translate( tileray tdir, const point &pivot, const point &p, point &q )
{
    tdir.clear_advance();
    tdir.advance( p.x - pivot.x );
    q.x = tdir.dx() + tdir.ortho_dx( p.y - pivot.y );
    q.y = tdir.dy() + tdir.ortho_dy( p.y - pivot.y );
}

void old_precalc_mounts( int dir, const point &pivot, std::vector<std::pair<point, point>> parts  )
{
    tileray tdir( dir );
    for( auto &p : parts ) {
        slow_coord_translate( tdir, pivot, p.first, p.second );
    }
}

void coord_translate( tileray tdir, point delta, const point &pivot, const point &p, point &q )
{
    q.x = delta.x + tdir.ortho_dx( p.y - pivot.y );
    q.y = delta.y + tdir.ortho_dy( p.y - pivot.y );
}


void new_precalc_mounts( int dir, const point &pivot, std::vector<std::pair<point, point>> parts  )
{
    tileray tdir( dir );
    std::map<int, point> offset_to_advance;
    for( auto &p : parts ) {
        auto r = offset_to_advance.find( p.first.x );
        if( r == offset_to_advance.end() ) {
            coord_translate( tdir, pivot, p.first, p.second );
            point advance = point( tdir.dx(), tdir.dy() ); 
            offset_to_advance.insert( { p.first.x, advance } );
        } else {
            coord_translate( tdir, r->second, pivot, p.first, p.second );
        }
    }
}

TEST_CASE( "test_coord_trans" )
{
    point pivot = point( 3, -4 );
    std::vector<std::pair<point, point>> parts_old;
    std::vector<std::pair<point, point>> parts_new;
    for( int i = 0; i < 7; i++ ) {
        for( int x = -5; x < 5; x++ ) {
            for( int y = -10; y < 9; y++ ) {
                point mount = point( x, y );
                parts_new.push_back( std::pair<point, point>( mount, mount ) );
                parts_old.push_back( std::pair<point, point>( mount, mount ) );
            }
        }
    }
    for( int dir = 0; dir < 360; dir += 1 ) {
        old_precalc_mounts( dir, pivot, parts_old );
        new_precalc_mounts( dir, pivot, parts_new );
        for( size_t i = 0; i < parts_old.size(); i++ ) {
            CHECK( parts_old[ i ].second.x == parts_new[ i ].second.x );
            CHECK( parts_old[ i ].second.y == parts_new[ i ].second.y );
        }
    }
}
 
