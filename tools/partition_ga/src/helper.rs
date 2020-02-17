use rand::{thread_rng, Rng};
use std::fmt::Debug;

pub fn print_vec<T: Debug>(v: &[T]) {
    for i in v.iter() { println!("{:?}", i); }   
}


pub fn select_index(cumulative_weights: &[f64]) -> usize {
    // TODO: Error Handling
    let w_sum = cumulative_weights.last().unwrap(); 
    let r: f64 = thread_rng().gen_range(0.0, *w_sum);
    cumulative_weights.iter().rposition(|&w| w < r).unwrap()
}
