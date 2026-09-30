# emojicon
[![Build Status](https://github.com/mominul/emojicon/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/mominul/emojicon/actions?query=branch%3Amain)
[![crates.io](https://img.shields.io/crates/v/emojicon.svg)](https://crates.io/crates/emojicon)
[![docs.rs](https://docs.rs/emojicon/badge.svg)](https://docs.rs/emojicon/0.4.0/emojicon/)
[![Rust](https://img.shields.io/badge/rust-1.56.0%2B-blue.svg?maxAge=3600)](https://blog.rust-lang.org/2021/10/21/Rust-1.56.0.html)

Find Emoji by using Emoticons and GitHub's, Bengali emoji names.

```rust
use emojicon::{Emojicon, BengaliEmoji};
fn main() {
    let emojicon = Emojicon::new();
    assert_eq!(emojicon.get_by_emoticon("B-)"), Some("😎"));
    assert_eq!(emojicon.get_by_name("cool").unwrap().collect::<Vec<_>>(), ["😎", "🆒"]);
    
    let emojis = BengaliEmoji::new();
    assert_eq!(emojis.get("কুল").unwrap().collect::<Vec<_>>(), ["🆒", "😎"]);
}
```

## Acknowledgment
* [emoticon](https://github.com/wooorm/emoticon) by Titus Wormer
* [gemoji](https://github.com/github/gemoji) by Github
* [bnemo](https://github.com/faruk-ahmad/bnemo) by Faruk Ahmad
