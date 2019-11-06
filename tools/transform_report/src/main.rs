use std::fs::File;
use quick_xml::Reader;
use quick_xml::events::Event;
use std::collections::HashMap;
use serde_json;
use serde::{Deserialize, Serialize};
use clap::App;
use counter::Counter;

const MAP: &str = "Comment        comment 
    ClubName       clubname 
    teamName       name 
    textbox15      gssa_id
    textbox16      program 
    textbox48      program2  
    textbox44      group  
    TeamStatus     status 
    BlackoutDates  blackout 
    textbox31      preferred_day 
    FlightPosition flt_pos 
    textbox49      flight 
    venue          venue 
    SubmissionDate submission_date";

type Team = HashMap<String, String>;

#[derive(Serialize, Deserialize)]
struct Division {
    teams: Vec<Team>,
}

fn read_and_filter(src: &str, filters: &HashMap<String, String>) -> Division {
    let mut data = Division{teams: Vec::new(),};

    let filename = format!("/repos/soccer_ng/season/{}.xml", src);
    let mut reader = Reader::from_file(filename).unwrap();
    reader.trim_text(true);
    let mut txt = Vec::new();
    let mut buf = Vec::new();

    let mut mapping = HashMap::new();
    for line in MAP.lines() {
        let vals:Vec<_> = line.split_whitespace().collect();
        mapping.insert(vals[0].to_string(), vals[1].to_string());
    }
    //let filters: HashMap<_, _> = vec![("flight".to_string(), "Competitive")].into_iter().collect();
    loop {
        match reader.read_event(&mut buf) {
            Ok(Event::Empty(ref e)) => {
                match e.name() {
                    b"Detail" => {
                        let mut fields:Team = HashMap::new();
                        for attr in e.attributes() {
                            let attr   = attr.unwrap();
                            let key    = format!("{}", String::from_utf8_lossy(attr.key));
                            let bvalue = attr.value.into_owned();
                            let value  = format!("{}", String::from_utf8_lossy(&bvalue));
                            if mapping.contains_key(&key) {
                                fields.insert(mapping[&key].clone(), value);
                            }
                        }
                        //println!("{:?}", fields);
                        let mut ok = true;   
                        for (k, v) in filters.iter() {
                            if !fields.contains_key(k) || !fields[k].contains(v) {
                                ok = false;
                            }
                        }
                        if ok {
                            data.teams.push(fields);
                        }
                    },
                    _ => {},
                }
            },
            Ok(Event::Text(e)) => txt.push(e.unescape_and_decode(&reader).unwrap()),
            Ok(Event::Eof) => break, 
            Err(e) => panic!("Error at position {}: {:?}", reader.buffer_position(), e),
            _ => (),
        }

        buf.clear();
    }
    data

}
fn show(data: &Division) {
    println!("\nInteresting Fields (number of items is between 1 and 10)");
    let mut attrs = Vec::new();
    for line in MAP.lines() {
        let vals:Vec<_> = line.split_whitespace().collect();
        let value = vals[1].to_string();
        attrs.push(value.clone());
    }
    for attr in attrs.iter() {
        let counts = data.teams
            .iter()
            .filter_map(|t| t.get(attr))
            .collect::<Counter<_>>()
            .most_common_ordered();
        if counts.len() > 1 && counts.len() < 10 { 
            let mut total = 0;
            println!("-- {} --", attr);
            for (val, count) in counts {
                total += count;
                println!("    {:3}: {}", count, val);
            }
            let missing = data.teams.len() - total;
            if missing > 0 {
                println!(r#"    {:3}: missing items"#, missing);
            }
        }
    }
}
fn main() {
    let mut mapping = HashMap::new();
    for line in MAP.lines() {
        let vals:Vec<_> = line.split_whitespace().collect();
        mapping.insert(vals[0].to_string(), vals[1].to_string());
    }

    // generate filter options from mapping table
    let filter_options = mapping.values()
                        .map(|v| format!("--{}= [{}] 'filter option'", v, v))
                        .collect::<Vec<String>>()
                        .join("\n");

    let matches = App::new("transform_report")
                    .version("0.1.0")
                    .author("Andrew Henshaw")
                    .about("Transform ADG report into JSON, with optional filtering.")
                    .args_from_usage("<INPUT>  'Sets the input base filename to use'
                                      -o --output [OUTPUT] 'Write output to JSON file'
                                      -s --show 'Show the count of attribute values")
                    .args_from_usage(&filter_options)
                    .get_matches();

    // extract the filter options that are specified by user
    let mut filters = HashMap::new();
    for v in mapping.values() {
        if let Some(value) = matches.value_of(v) {
            filters.insert(v.to_string(), value.to_string());
        }
    }

    let input    = matches.value_of("INPUT").unwrap();
    let data     = read_and_filter(input, &filters);
    if matches.is_present("show") {
        show(&data);
    }
    if let Some(output) = matches.value_of("output") {
        let filename = format!("/repos/soccer_ng/season/{}.json", output);
        let outfile  = File::create(&filename).unwrap();
        let _result  = serde_json::to_writer_pretty(outfile, &data);
        println!("\nCreated {}\n{} teams written", &filename, data.teams.len());
    }

}