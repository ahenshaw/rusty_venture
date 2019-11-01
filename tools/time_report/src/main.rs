use svg::Document;
use svg::node::element::{Rectangle, Group, Text};
type Times = Vec<i32>;

fn time_bar(t:Times) -> Group {
    let mut group = Group::new();

    let mut x = 0;
    for width in t.iter() {
        let rect = Rectangle::new()
            .set("fill", "yellow")
            .set("stroke", "black")
            .set("stroke-width", 0.5)
            .set("width", *width)
            .set("height", 5)
            .set("x", x)
            .set("y", 10);
        group = group.add(rect);
        x += width;
    }
    group
}

fn main() {
    let t:Times = vec![12, 0, 3, 5, 10];
    let text = Text::new()
               .set("x", 0)
               .set("y", 0);
    let document = Document::new()
        .set("viewBox", (0, 0, 400, 120))
        .add(text)
        .add(time_bar(t));

    svg::save("image.svg", &document).unwrap();
}
