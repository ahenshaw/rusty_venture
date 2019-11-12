use sqlite::Value;
use std::fs::File;
use std::collections::{HashMap, HashSet};
use serde_json;
use serde::{Deserialize, Serialize};
use clap::{Arg, App};

const SQL_CLUB: &str  = "SELECT id FROM club WHERE name=?";
const SQL_VENUE: &str = "SELECT venue_id, venue.name, venue.lat, venue.lon
                         FROM club_venue 
                         JOIN venue ON venue_id=venue.id
                         WHERE club_id=?";
const SQL_COST: &str  = "SELECT away_id, cost FROM venue_venue 
                         WHERE home_id=?";

const DB: &str = "/repos/soccer/data/soccer.db";

type Team = HashMap<String, String>;

#[derive(Serialize, Deserialize)]
struct Division {
    teams: Vec<Team>,
    #[serde(default)]
    costs: HashMap<i64, HashMap<i64, i64>>,
}

fn add_venues(data: &mut Division) -> bool {
    let connection = sqlite::open(DB).unwrap();
    let mut cursor = connection.prepare(SQL_CLUB).unwrap().cursor();
    let mut cursor2 = connection.prepare(SQL_VENUE).unwrap().cursor();

    let mut is_ok = true;

    for team in data.teams.iter_mut() {
        let clubname = &team["clubname"];
        cursor.bind(&[Value::String(clubname.to_string())]).unwrap();
        match cursor.next().unwrap() {
            Some(row) => {
                let club_id = row[0].as_integer().unwrap();
                team.insert("club_id".to_string(), format!("{}", club_id));
                cursor2.bind(&[Value::Integer(club_id)]).unwrap();
                match cursor2.next().unwrap(){
                    Some(record) => {
                        if let [venue_id, venue, lat, lon] = &record {
                            team.insert("venue_id".to_string(), format!("{}", venue_id.as_integer().unwrap()));
                            team.insert("venue".to_string(), venue.as_string().unwrap().to_string());
                            team.insert("lat".to_string(), format!("{}", lat.as_float().unwrap()));
                            team.insert("lon".to_string(), format!("{}", lon.as_float().unwrap()));
                        };
                    },
                    None => {},
                }
            },
            None => {
                println!("{} not found", clubname);
                is_ok = false;
            },
        }
    }
    is_ok
}

fn add_costs(data: &mut Division) {
    let connection = sqlite::open(DB).unwrap();
    let mut cursor = connection.prepare(SQL_COST).unwrap().cursor();

    let mut venues =  HashSet::new();
    let mut costs  =  HashMap::new();
    for team in data.teams.iter() {
        venues.insert(team["venue_id"].parse::<i64>().unwrap());
    }
    for home_id in venues.iter() {
        let mut these_costs =  HashMap::new();
        cursor.bind(&[Value::Integer(*home_id)]).unwrap();
        while let Some(record) = cursor.next().unwrap() {
            let away_id = record[0].as_integer().unwrap();
            let cost    = record[1].as_integer().unwrap();
            if venues.contains(&away_id) {
                these_costs.insert(away_id, cost);
            }
        }
        costs.insert(*home_id, these_costs);
    }
    data.costs = costs;
}

fn main() {
    let params = App::new("Add Venues")
                      .version("1.0")
                      .author("Andrew Henshaw")
                      .about("Adds venue info to Division JSON file")
                      .arg(Arg::with_name("DIVISION")
                          .help("Specifies the Division name")
                          .required(true)
                          .index(1))
                      .get_matches();


    if let Some(division) = params.value_of("DIVISION") {
        let filename = format!("{}.json", division);
        let infile = File::open(&filename).unwrap();
        let mut data:Division = serde_json::from_reader(infile).unwrap();
        if add_venues(&mut data) {
            let outfile = File::create(&filename).unwrap();
            add_costs(&mut data);
            let _result = serde_json::to_writer_pretty(outfile, &data);
        }
    }
}
