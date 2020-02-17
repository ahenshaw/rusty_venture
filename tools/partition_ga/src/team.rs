use mysql;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Team {
    pub team_id: u32,
    pub venue_id: u32,
    pub flt_pos: String,
}

impl Team {

    // pub fn new(id: usize) -> Self {
    //     Team { team_id: id as u32 }
    // }

    pub fn cost(&self, other: &Team) -> f64 {
        ((self.team_id as f64) - (other.team_id as f64)).abs()
    }
}

pub fn get_teams(db: &mysql::Pool, division_id: u32) -> Vec<Team> {
    let teams: Vec<Team> = 
    db.prep_exec("SELECT id, venue_id, name FROM team WHERE division_id=?", (division_id,))
    .map(|result| { 
        result.map(|x| x.unwrap()).map(|row| {
            let (team_id, venue_id, flt_pos) = mysql::from_row(row);
            Team{team_id, venue_id, flt_pos,}
        }).collect() 
    }).unwrap(); 
    teams
}


