// Bongo Engine - Linux Input Method & Phonetic Service
// Connects the riti core engine to Linux input methods (IBus / Fcitx5).

extern crate riti;

use std::ffi::CString;
use std::os::raw::c_char;

use riti::config::Config;
use riti::context::RitiContext;
pub use riti::keycodes;
use riti::suggestion::Suggestion;

#[repr(u32)]
#[derive(Copy, Clone, Debug, PartialEq)]
pub enum TypingMode {
    PhoneticFirst = 0,
    Smart = 1,
    PhoneticOnly = 2,
}

pub struct BongoLinuxEngine {
    main_ctx: RitiContext,
    shadow_ctx: Option<RitiContext>,
    main_config: Config,
    shadow_config: Config,
    mode: TypingMode,
    show_emoji: bool,
    current_phonetic: Option<String>,
}

fn configs_for(mode: TypingMode, show_emoji: bool) -> (Config, Config) {
    let mut main_config = Config::default();
    main_config.set_layout_file_path("avro_phonetic");
    main_config.set_phonetic_suggestion(mode != TypingMode::PhoneticOnly);
    main_config.set_include_emoji(show_emoji);

    let mut shadow_config = Config::default();
    shadow_config.set_layout_file_path("avro_phonetic");
    shadow_config.set_phonetic_suggestion(false);
    shadow_config.set_include_emoji(false);

    (main_config, shadow_config)
}

/// Convert a Unicode character codepoint to a riti keycode.
#[no_mangle]
pub extern "C" fn avro_keycode_for_char(ch: u32) -> u16 {
    match char::from_u32(ch) {
        Some('`') => riti::keycodes::VC_GRAVE,
        Some('~') => riti::keycodes::VC_TILDE,
        Some('1') => riti::keycodes::VC_1,
        Some('2') => riti::keycodes::VC_2,
        Some('3') => riti::keycodes::VC_3,
        Some('4') => riti::keycodes::VC_4,
        Some('5') => riti::keycodes::VC_5,
        Some('6') => riti::keycodes::VC_6,
        Some('7') => riti::keycodes::VC_7,
        Some('8') => riti::keycodes::VC_8,
        Some('9') => riti::keycodes::VC_9,
        Some('0') => riti::keycodes::VC_0,
        Some('!') => riti::keycodes::VC_EXCLAIM,
        Some('@') => riti::keycodes::VC_AT,
        Some('#') => riti::keycodes::VC_HASH,
        Some('$') => riti::keycodes::VC_DOLLAR,
        Some('%') => riti::keycodes::VC_PERCENT,
        Some('^') => riti::keycodes::VC_CIRCUM,
        Some('&') => riti::keycodes::VC_AMPERSAND,
        Some('*') => riti::keycodes::VC_ASTERISK,
        Some('(') => riti::keycodes::VC_PAREN_LEFT,
        Some(')') => riti::keycodes::VC_PAREN_RIGHT,
        Some('-') => riti::keycodes::VC_MINUS,
        Some('_') => riti::keycodes::VC_UNDERSCORE,
        Some('=') => riti::keycodes::VC_EQUALS,
        Some('+') => riti::keycodes::VC_PLUS,
        Some('a') => riti::keycodes::VC_A,
        Some('b') => riti::keycodes::VC_B,
        Some('c') => riti::keycodes::VC_C,
        Some('d') => riti::keycodes::VC_D,
        Some('e') => riti::keycodes::VC_E,
        Some('f') => riti::keycodes::VC_F,
        Some('g') => riti::keycodes::VC_G,
        Some('h') => riti::keycodes::VC_H,
        Some('i') => riti::keycodes::VC_I,
        Some('j') => riti::keycodes::VC_J,
        Some('k') => riti::keycodes::VC_K,
        Some('l') => riti::keycodes::VC_L,
        Some('m') => riti::keycodes::VC_M,
        Some('n') => riti::keycodes::VC_N,
        Some('o') => riti::keycodes::VC_O,
        Some('p') => riti::keycodes::VC_P,
        Some('q') => riti::keycodes::VC_Q,
        Some('r') => riti::keycodes::VC_R,
        Some('s') => riti::keycodes::VC_S,
        Some('t') => riti::keycodes::VC_T,
        Some('u') => riti::keycodes::VC_U,
        Some('v') => riti::keycodes::VC_V,
        Some('w') => riti::keycodes::VC_W,
        Some('x') => riti::keycodes::VC_X,
        Some('y') => riti::keycodes::VC_Y,
        Some('z') => riti::keycodes::VC_Z,
        Some('A') => riti::keycodes::VC_A_SHIFT,
        Some('B') => riti::keycodes::VC_B_SHIFT,
        Some('C') => riti::keycodes::VC_C_SHIFT,
        Some('D') => riti::keycodes::VC_D_SHIFT,
        Some('E') => riti::keycodes::VC_E_SHIFT,
        Some('F') => riti::keycodes::VC_F_SHIFT,
        Some('G') => riti::keycodes::VC_G_SHIFT,
        Some('H') => riti::keycodes::VC_H_SHIFT,
        Some('I') => riti::keycodes::VC_I_SHIFT,
        Some('J') => riti::keycodes::VC_J_SHIFT,
        Some('K') => riti::keycodes::VC_K_SHIFT,
        Some('L') => riti::keycodes::VC_L_SHIFT,
        Some('M') => riti::keycodes::VC_M_SHIFT,
        Some('N') => riti::keycodes::VC_N_SHIFT,
        Some('O') => riti::keycodes::VC_O_SHIFT,
        Some('P') => riti::keycodes::VC_P_SHIFT,
        Some('Q') => riti::keycodes::VC_Q_SHIFT,
        Some('R') => riti::keycodes::VC_R_SHIFT,
        Some('S') => riti::keycodes::VC_S_SHIFT,
        Some('T') => riti::keycodes::VC_T_SHIFT,
        Some('U') => riti::keycodes::VC_U_SHIFT,
        Some('V') => riti::keycodes::VC_V_SHIFT,
        Some('W') => riti::keycodes::VC_W_SHIFT,
        Some('X') => riti::keycodes::VC_X_SHIFT,
        Some('Y') => riti::keycodes::VC_Y_SHIFT,
        Some('Z') => riti::keycodes::VC_Z_SHIFT,
        Some('[') => riti::keycodes::VC_BRACKET_LEFT,
        Some(']') => riti::keycodes::VC_BRACKET_RIGHT,
        Some('\\') => riti::keycodes::VC_BACK_SLASH,
        Some('{') => riti::keycodes::VC_BRACE_LEFT,
        Some('}') => riti::keycodes::VC_BRACE_RIGHT,
        Some('|') => riti::keycodes::VC_BAR,
        Some(';') => riti::keycodes::VC_SEMICOLON,
        Some('\'') => riti::keycodes::VC_APOSTROPHE,
        Some(',') => riti::keycodes::VC_COMMA,
        Some('.') => riti::keycodes::VC_PERIOD,
        Some('/') => riti::keycodes::VC_SLASH,
        Some(':') => riti::keycodes::VC_COLON,
        Some('"') => riti::keycodes::VC_QUOTE,
        Some('<') => riti::keycodes::VC_LESS,
        Some('>') => riti::keycodes::VC_GREATER,
        Some('?') => riti::keycodes::VC_QUESTION,
        _ => 0,
    }
}

/// Creates a new BongoLinuxEngine instance with defaults.
#[no_mangle]
pub extern "C" fn bongo_engine_new() -> *mut BongoLinuxEngine {
    let mode = TypingMode::PhoneticFirst;
    let show_emoji = true;
    let (main_config, shadow_config) = configs_for(mode, show_emoji);
    let main_ctx = RitiContext::new_with_config(&main_config);
    let shadow_ctx = Some(RitiContext::new_with_config(&shadow_config));

    let engine = BongoLinuxEngine {
        main_ctx,
        shadow_ctx,
        main_config,
        shadow_config,
        mode,
        show_emoji,
        current_phonetic: None,
    };

    Box::into_raw(Box::new(engine))
}

/// Frees the engine.
#[no_mangle]
pub extern "C" fn bongo_engine_free(engine: *mut BongoLinuxEngine) {
    if !engine.is_null() {
        unsafe {
            drop(Box::from_raw(engine));
        }
    }
}

/// Sets typing mode: 0 = PhoneticFirst, 1 = Smart, 2 = PhoneticOnly.
#[no_mangle]
pub extern "C" fn bongo_engine_set_mode(engine: *mut BongoLinuxEngine, mode: u32) {
    if engine.is_null() {
        return;
    }
    let eng = unsafe { &mut *engine };
    let new_mode = match mode {
        1 => TypingMode::Smart,
        2 => TypingMode::PhoneticOnly,
        _ => TypingMode::PhoneticFirst,
    };
    if eng.mode == new_mode {
        return;
    }

    eng.mode = new_mode;
    eng.main_config
        .set_phonetic_suggestion(new_mode != TypingMode::PhoneticOnly);
    eng.main_ctx.update_engine(&eng.main_config);
    if let Some(ref mut shadow) = eng.shadow_ctx {
        shadow.update_engine(&eng.shadow_config);
    }
    eng.main_ctx.finish_input_session();
    if let Some(ref mut shadow) = eng.shadow_ctx {
        shadow.finish_input_session();
    }
    eng.current_phonetic = None;
}

/// Toggles emoji suggestions.
#[no_mangle]
pub extern "C" fn bongo_engine_set_emoji(engine: *mut BongoLinuxEngine, enabled: bool) {
    if engine.is_null() {
        return;
    }
    let eng = unsafe { &mut *engine };
    if eng.show_emoji == enabled {
        return;
    }

    eng.show_emoji = enabled;
    eng.main_config.set_include_emoji(enabled);
    eng.main_ctx.update_engine(&eng.main_config);
    if let Some(ref mut shadow) = eng.shadow_ctx {
        shadow.update_engine(&eng.shadow_config);
    }
}

/// Checks if there is an active composing session.
#[no_mangle]
pub extern "C" fn bongo_engine_has_session(engine: *mut BongoLinuxEngine) -> bool {
    if engine.is_null() {
        return false;
    }
    let eng = unsafe { &*engine };
    eng.main_ctx.ongoing_input_session()
}

fn extract_top_text(s: &Suggestion) -> Option<String> {
    match s {
        Suggestion::Full { suggestions, .. } => suggestions.first().cloned(),
        Suggestion::Single { suggestion, .. } => {
            if suggestion.is_empty() {
                None
            } else {
                Some(suggestion.clone())
            }
        }
    }
}

/// Feeds a character codepoint. Returns a pointer to Suggestion.
#[no_mangle]
pub extern "C" fn bongo_engine_feed_char(
    engine: *mut BongoLinuxEngine,
    ch: u32,
    modifier: u8,
    selection: u8,
) -> *mut Suggestion {
    if engine.is_null() {
        return std::ptr::null_mut();
    }
    let eng = unsafe { &mut *engine };
    let keycode = avro_keycode_for_char(ch);
    if keycode == 0 {
        return std::ptr::null_mut();
    }

    let suggestion = eng
        .main_ctx
        .get_suggestion_for_key(keycode, modifier, selection);

    if let Some(ref mut shadow) = eng.shadow_ctx {
        let shadow_sugg = shadow.get_suggestion_for_key(keycode, modifier, 0);
        eng.current_phonetic = extract_top_text(&shadow_sugg);
    }

    Box::into_raw(Box::new(suggestion))
}

/// Feeds a backspace event.
#[no_mangle]
pub extern "C" fn bongo_engine_backspace(
    engine: *mut BongoLinuxEngine,
    whole_word: bool,
) -> *mut Suggestion {
    if engine.is_null() {
        return std::ptr::null_mut();
    }
    let eng = unsafe { &mut *engine };
    let suggestion = eng.main_ctx.backspace_event(whole_word);

    if let Some(ref mut shadow) = eng.shadow_ctx {
        let shadow_sugg = shadow.backspace_event(whole_word);
        eng.current_phonetic = extract_top_text(&shadow_sugg);
    }

    Box::into_raw(Box::new(suggestion))
}

/// Commits candidate at given index and finishes session.
#[no_mangle]
pub extern "C" fn bongo_engine_commit(engine: *mut BongoLinuxEngine, index: usize) {
    if engine.is_null() {
        return;
    }
    let eng = unsafe { &mut *engine };
    if eng.mode == TypingMode::Smart {
        eng.main_ctx.candidate_committed(index);
    }
    eng.main_ctx.finish_input_session();
    if let Some(ref mut shadow) = eng.shadow_ctx {
        shadow.finish_input_session();
    }
    eng.current_phonetic = None;
}

/// Resets / cancels the active session without committing.
#[no_mangle]
pub extern "C" fn bongo_engine_reset(engine: *mut BongoLinuxEngine) {
    if engine.is_null() {
        return;
    }
    let eng = unsafe { &mut *engine };
    eng.main_ctx.finish_input_session();
    if let Some(ref mut shadow) = eng.shadow_ctx {
        shadow.finish_input_session();
    }
    eng.current_phonetic = None;
}

// MARK: - Suggestion Inspection Helpers

#[no_mangle]
pub extern "C" fn bongo_suggestion_count(suggestion: *const Suggestion) -> usize {
    if suggestion.is_null() {
        return 0;
    }
    let s = unsafe { &*suggestion };
    match s {
        Suggestion::Full { suggestions, .. } => suggestions.len(),
        Suggestion::Single { suggestion, .. } => {
            if suggestion.is_empty() {
                0
            } else {
                1
            }
        }
    }
}

/// Gets candidate at index. Returns owned C string pointer. Must be freed with `bongo_string_free`.
#[no_mangle]
pub extern "C" fn bongo_suggestion_get_candidate(
    suggestion: *const Suggestion,
    index: usize,
) -> *mut c_char {
    if suggestion.is_null() {
        return std::ptr::null_mut();
    }
    let s = unsafe { &*suggestion };
    let cand_str: Option<&str> = match s {
        Suggestion::Full { suggestions, .. } => suggestions.get(index).map(|x| x.as_str()),
        Suggestion::Single { suggestion, .. } => {
            if index == 0 && !suggestion.is_empty() {
                Some(suggestion.as_str())
            } else {
                None
            }
        }
    };
    if let Some(cand) = cand_str {
        if let Ok(c_str) = CString::new(cand) {
            return c_str.into_raw();
        }
    }
    std::ptr::null_mut()
}

/// Gets top candidate or lonely text.
#[no_mangle]
pub extern "C" fn bongo_suggestion_get_preview(suggestion: *const Suggestion) -> *mut c_char {
    if suggestion.is_null() {
        return std::ptr::null_mut();
    }
    let s = unsafe { &*suggestion };
    let cand_str: Option<&str> = match s {
        Suggestion::Full { suggestions, .. } => suggestions.first().map(|x| x.as_str()),
        Suggestion::Single { suggestion, .. } => {
            if !suggestion.is_empty() {
                Some(suggestion.as_str())
            } else {
                None
            }
        }
    };
    if let Some(txt) = cand_str {
        if let Ok(c_str) = CString::new(txt) {
            return c_str.into_raw();
        }
    }
    std::ptr::null_mut()
}

#[no_mangle]
pub extern "C" fn bongo_suggestion_free(suggestion: *mut Suggestion) {
    if !suggestion.is_null() {
        unsafe {
            drop(Box::from_raw(suggestion));
        }
    }
}

#[no_mangle]
pub extern "C" fn bongo_string_free(s: *mut c_char) {
    if !s.is_null() {
        unsafe {
            drop(CString::from_raw(s));
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::ffi::CStr;

    fn options(engine: *mut BongoLinuxEngine, keys: &[char]) -> Vec<String> {
        let mut suggestion: *mut Suggestion = std::ptr::null_mut();
        for ch in keys {
            if !suggestion.is_null() {
                bongo_suggestion_free(suggestion);
            }
            suggestion = bongo_engine_feed_char(engine, *ch as u32, 0, 0);
        }

        let mut result = Vec::new();
        if !suggestion.is_null() {
            for index in 0..bongo_suggestion_count(suggestion) {
                let ptr = bongo_suggestion_get_candidate(suggestion, index);
                if !ptr.is_null() {
                    let text = unsafe { CStr::from_ptr(ptr) }
                        .to_string_lossy()
                        .into_owned();
                    result.push(text);
                    bongo_string_free(ptr);
                }
            }
            bongo_suggestion_free(suggestion);
        }
        result
    }

    #[test]
    fn phonetic_only_returns_a_single_direct_transliteration() {
        let engine = bongo_engine_new();
        bongo_engine_set_mode(engine, 2);
        let candidates = options(engine, &['a', 'm', 'i']);
        assert_eq!(candidates, vec!["আমি"]);
        bongo_engine_free(engine);
    }

    #[test]
    fn phonetic_first_returns_dictionary_candidates() {
        let engine = bongo_engine_new();
        bongo_engine_set_mode(engine, 0);
        let candidates = options(engine, &['a', 'm', 'i']);
        assert!(candidates.len() > 1, "candidates: {candidates:?}");
        bongo_engine_free(engine);
    }

    #[test]
    fn emoji_setting_controls_emoji_candidates() {
        let engine = bongo_engine_new();

        bongo_engine_set_emoji(engine, true);
        let with_emoji = options(engine, &[':', ')']);
        assert!(
            with_emoji.iter().any(|candidate| candidate.contains('😃')),
            "candidates: {with_emoji:?}"
        );

        bongo_engine_reset(engine);
        bongo_engine_set_emoji(engine, false);
        let without_emoji = options(engine, &[':', ')']);
        assert!(
            !without_emoji
                .iter()
                .any(|candidate| candidate.contains('😃')),
            "candidates: {without_emoji:?}"
        );

        bongo_engine_free(engine);
    }
}
