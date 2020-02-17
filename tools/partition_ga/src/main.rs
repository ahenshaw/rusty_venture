use mysql;
use std::collections::HashMap;

extern crate partition_ga;
use partition_ga::{Team, Simulation};
use partition_ga::team::get_teams;

#[derive(Debug, PartialEq, Eq)]
struct TeamInfo {
    team_id: u32,
    venue_id: u32,
    flt_pos: String,
}

#[derive(Debug, PartialEq, Eq)]
struct Weight {
    home_id: u32,
    away_id: u32,
    cost   : u32,
}

#[allow(dead_code)]
fn get_weights(db: &mysql::Pool, teams: &Vec<Team>) -> HashMap<(u32, u32), u32> {
    let costs: HashMap<(u32, u32), u32> = 
        db.prep_exec("SELECT home_id, away_id, cost FROM venue_venue", ())
        .map(|result| { 
            result.map(|x| x.unwrap()).map(|row| {
                let (home_id, away_id, cost) = mysql::from_row(row);
                ((home_id, away_id), cost)
            }).collect() 
        }).unwrap(); 

    let mut weights = HashMap::new();
    for t1 in teams {
        for t2 in teams {
            let mut w = 100000;
            if t1 != t2  {
                w = costs[&(t1.venue_id, t2.venue_id)];
            }
            weights.insert((t1.team_id, t2.team_id), w) ;
        }
    }
    weights
}


fn main() {
    println!("Querying database...");
    let db = mysql::Pool::new("mysql://soccer_admin:smyrna@soccer.henshaw.us:3306/soccer").unwrap();
    let teams = get_teams(&db, 2);
    let weights = get_weights(&db, &teams);
    let groups = vec![6,6,6,5];
    //println!("{:?}", weights);
    let skip = 1000;
    let iterations = 1000000;
    let population_size =  30;
    let crossover_probability = 1.0;
    let mutation_probability = 0.4;

    // ----------------------
    // RUN SIMULATION
    // ----------------------
    let mut sim = Simulation::new(
        iterations,
        crossover_probability, 
        mutation_probability, 
        population_size,
        teams,
        weights,
        groups
    );

    sim.run(skip);
}
