use rand::{thread_rng, Rng};
use super::*; 
use helper::print_vec;
use std::collections::HashMap;
use std::time::{Duration, Instant};

pub struct Simulation {
    iterations: usize,

    crossover_probability: f64,
    mutation_probability:  f64,
    population_size:       usize, 

    number_of_teams: usize,
    teams:           Vec<Team>,
    groups:          Vec<usize>,
    weights:         HashMap<(u32, u32), u32>,

    number_of_mutations:  usize,
    number_of_crossovers: usize,

    pub fitness: f64,
    pub dna:     Vec<usize>, 
}

impl Simulation {

    pub fn new(iterations: usize,
               crossover_probability: f64,
               mutation_probability: f64,
               population_size: usize,
               teams: Vec<Team>,
               weights: HashMap<(u32, u32), u32>,
               groups: Vec<usize>) -> Self {

        let number_of_teams = teams.len();
        let number_of_mutations  = 0;
        let number_of_crossovers = 0;
        let fitness = -1000000.0;
        let dna: Vec<usize> = Vec::new(); 

        Simulation { 
            iterations, 
            crossover_probability, 
            mutation_probability, 
            population_size, 
            number_of_teams, 
            teams,
            weights,
            groups,
            number_of_mutations,
            number_of_crossovers,
            fitness,
            dna,
        }
    }

    fn generate_children(&mut self, 
                         mom: &Individual, 
                         dad: &Individual) -> (Individual, Individual) {
        if thread_rng().gen_bool(self.crossover_probability) {
            self.number_of_crossovers += 2;
            mom.cross_over(dad, &self.teams, &self.weights, &self.groups)
        } else {
            (mom.clone(), dad.clone())
        }
    }

    fn might_mutate_child(&mut self, child: &mut Individual) {
        if thread_rng().gen_bool(self.mutation_probability) {
            child.mutate(&self.teams, &self.weights, &self.groups);
            self.number_of_mutations += 1;
        }
    }

    pub fn generate_population(&mut self, individuals: Vec<Individual>) -> Vec<Individual> {
        assert_eq!(self.population_size % 2, 0, "population_size:{} should be divisible by 2", self.population_size);
        
        let cumulative_weights = get_cumulative_weights(&individuals);
        let mut next_population = Vec::new();

        for _ in 0..(self.population_size / 2 ) { // generate two individuals per iteration 

            let (mom, dad) = select_parents(&cumulative_weights, &individuals);
            let (mut daughter, mut son) = self.generate_children(&mom, &dad);
            self.might_mutate_child(&mut daughter);
            self.might_mutate_child(&mut son);

            next_population.push(daughter);
            next_population.push(son);
        }
        next_population
    }

    pub fn run(&mut self, skip: usize) {
        let now = Instant::now();

        assert!(skip > 0, "skip must be 1 or larger");

        let mut population = random_population(self.population_size, &self.teams, &self.weights, &self.groups);
        let mut champion = find_fittest(&population);

        for i in 0..self.iterations {

            let challenger = find_fittest(&population);
            population = self.generate_population(population);
            debug_print(now.elapsed(), skip, i + 1, &population, &champion, &challenger, &self.teams, &self.weights);

            if champion.fitness <= challenger.fitness {
                champion = challenger;
            }
        }

        self.fitness = champion.fitness;
        self.dna = champion.dna;
    }

    pub fn print(&self) {

        let x = self.population_size * self.iterations;

        println!("\n --------------- \n STATS \n --------------- \n");
        println!("BEST GROUPING: {:?}", self.dna);
        println!("Fitness Score: {} ", self.fitness);
        println!("{} mutations out of {} individuals produced", self.number_of_mutations, x);
        println!("{} cross-overs out of {} individuals produced", self.number_of_crossovers, x);

        println!("\n --------------- \n SPECS \n --------------- \n");
        println!("iterations: {:?}", self.iterations);
        println!("crossover_probability: {:?}", self.crossover_probability);
        println!("mutation_probability: {:?}", self.mutation_probability);
        println!("population_size: {:?}", self.population_size);
        println!("number_of_teams: {:?}", self.number_of_teams);
        println!("\n teams: ");
        print_vec(&self.teams);

        println!("\n --------------- \n END \n --------------- \n");

    }
}

fn debug_print(elapsed: Duration, skip: usize, 
               i: usize, 
               _population: &[Individual],
               champion: &Individual, 
               _challenger: &Individual, 
               _teams: &Vec<Team>,
               _weights: &HashMap<(u32, u32), u32>,
            ) {

    if i % skip == 0 {
        println!("{:?} {:4}, {:0.1}", elapsed, i, 1.0/champion.fitness);
        // let mut index = 0;
        // for count in [6,6,6,5].iter() {
        //     for i in (index..index+count) {
        //         let t = &teams[champion.dna[i]];
        //         println!("{}, {}", t.team_id, t.flt_pos);
        //     }
        //     println!();
        //     index += count;
        // }
    }
}