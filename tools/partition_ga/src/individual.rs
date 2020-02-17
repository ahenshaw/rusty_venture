use std::collections::HashMap;
use itertools::Itertools;
use super::Team;
use rand::{thread_rng, Rng};

#[derive(Debug, Clone)]
pub struct Individual {
    pub dna: Vec<usize>,
    pub fitness: f64,
}

impl Individual {

    pub fn new(dna: Vec<usize>, 
               teams:   &[Team], 
               weights: &HashMap<(u32, u32), u32>, 
               groups:  &[usize]) -> Self {
        let fitness = fitness(&dna, teams, weights, groups);
        Individual{dna, fitness}
    }

    pub fn cross_over(&self, 
                      other:   &Individual, 
                      teams:   &[Team], 
                      weights: &HashMap<(u32, u32), u32>, 
                      groups:  &[usize]) -> (Self, Self) {

        let n = self.dna.len();
        let mut rng = thread_rng();
        let start = rng.gen_range(0, n - 1);
        let end = rng.gen_range(start + 1, n);

        let daughter_dna = crossover_dna(&self.dna, &other.dna, start, end);
        let son_dna      = crossover_dna(&other.dna, &self.dna, start, end);
        
        let daughter = Individual::new(daughter_dna, teams, weights, groups);
        let son      = Individual::new(son_dna, teams, weights, groups);
        
        (daughter, son)
    }

    pub fn mutate(&mut self, 
                  teams:   &[Team], 
                  weights: &HashMap<(u32, u32), u32>, 
                  groups:  &[usize]) {
        let i = thread_rng().gen_range(0, self.dna.len() - 1);
        self.dna.swap(i, i + 1);
        self.fitness = fitness(&self.dna, teams, weights, groups);
    }
}

fn fitness(dna: &[usize], 
           teams: &[Team], 
           weights: &HashMap<(u32, u32), u32>, 
           groups: &[usize]) -> f64 {

    let mut index = 0;
    let mut total: u32 = 0;
    let mut counter = 0;
    for count in groups {
        let grp = &dna[index..index+count];
        total += grp.iter()
                      .tuple_combinations()
                      .map(|(&x, &y)| weights[&(teams[x].team_id, teams[y].team_id)]+weights[&(teams[y].team_id, teams[x].team_id)])
                      .sum::<u32>();
        index += count;
        counter += grp.iter().tuple_combinations().collect::<Vec<(&usize, &usize)>>().len();
    }
    assert!(counter==55);
    1.0/(total as f64)
}

fn crossover_dna(mom: &[usize], dad: &[usize], start: usize, end: usize) -> Vec<usize> {
    
    let mom_slice = &mom[start..=end];
    let mut child: Vec<usize> = Vec::new();
    
    for i in 0..dad.len() {
        if !mom_slice.contains(&dad[i]) {
            child.push(dad[i]);
        }
    }
    
    let end_slice = &child.split_off(start);
    child.extend_from_slice(mom_slice);
    child.extend_from_slice(end_slice);
    child
}

