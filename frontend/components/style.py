"""
Global QSS stylesheet for the ChatGPT-style dark UI.

Usage:
    from frontend.components.style import APP_STYLESHEET
    app.setStyleSheet(APP_STYLESHEET)
"""

# Color palette — matches modern ChatGPT dark theme
COLORS = {
    "sidebar_bg": "#171717",
    "main_bg": "#212121",
    "input_bg": "#2f2f2f",
    "input_border": "#3a3a3a",
    "user_bubble": "#2f2f2f",
    "assistant_bubble": "transparent",
    "border": "#3a3a3a",
    "border_light": "#565869",
    "text_primary": "#ececec",
    "text_secondary": "#8e8ea0",
    "text_muted": "#6b6b7b",
    "accent": "#10a37f",          # ChatGPT green
    "accent_hover": "#1abc8f",
    "button_hover": "#2a2a2a",
    "button_active": "#2f2f2f",
    "scrollbar_bg": "transparent",
    "scrollbar_handle": "#3a3a3a",
    "danger": "#e34040",
    "send_btn_disabled": "#404040",
}

APP_STYLESHEET = f"""
/* =========================================================
   Base — applied to all widgets
   ========================================================= */

QWidget {{
    background-color: {COLORS["main_bg"]};
    color: {COLORS["text_primary"]};
    font-family: "Segoe UI", "Inter", system-ui, sans-serif;
    font-size: 14px;
    border: none;
    outline: none;
}}

QMainWindow {{
    background-color: {COLORS["main_bg"]};
}}

/* =========================================================
   Sidebar
   ========================================================= */

QWidget#sidebar {{
    background-color: {COLORS["sidebar_bg"]};
}}

/* Sidebar header row */
QWidget#sidebarHeader {{
    background-color: {COLORS["sidebar_bg"]};
}}

QPushButton#sidebarToggleBtn {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    border: none;
    border-radius: 6px;
    padding: 6px;
    font-size: 16px;
    min-width: 30px;
    min-height: 30px;
    max-width: 30px;
    max-height: 30px;
}}

QPushButton#sidebarToggleBtn:hover {{
    background-color: {COLORS["button_hover"]};
    color: {COLORS["text_primary"]};
}}

QPushButton#newChatBtn {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    border: none;
    border-radius: 6px;
    padding: 6px;
    font-size: 16px;
    min-width: 30px;
    min-height: 30px;
    max-width: 30px;
    max-height: 30px;
}}

QPushButton#newChatBtn:hover {{
    background-color: {COLORS["button_hover"]};
    color: {COLORS["text_primary"]};
}}

QPushButton#searchBtn {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    text-align: left;
    font-size: 13px;
}}

QPushButton#searchBtn:hover {{
    background-color: {COLORS["button_hover"]};
    color: {COLORS["text_primary"]};
}}

QListWidget#historyList {{
    background-color: transparent;
    border: none;
    padding: 4px 0;
    outline: none;
}}

QListWidget#historyList::item {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    padding: 8px 10px;
    border-radius: 6px;
    margin: 1px 6px;
    font-size: 13px;
}}

QListWidget#historyList::item:hover {{
    background-color: {COLORS["button_hover"]};
    color: {COLORS["text_primary"]};
}}

QListWidget#historyList::item:selected {{
    background-color: {COLORS["button_active"]};
    color: {COLORS["text_primary"]};
}}

/* History section label */
QLabel#historySectionLabel {{
    color: {COLORS["text_muted"]};
    font-size: 11px;
    font-weight: 600;
    background: transparent;
}}

QPushButton#modeBtn {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    text-align: left;
    font-size: 13px;
}}

QPushButton#modeBtn:hover {{
    background-color: {COLORS["button_hover"]};
    color: {COLORS["text_primary"]};
}}

QPushButton#modeBtn:checked {{
    background-color: {COLORS["button_active"]};
    color: {COLORS["text_primary"]};
}}

QPushButton#settingsBtn {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    text-align: left;
    font-size: 13px;
}}

QPushButton#settingsBtn:hover {{
    background-color: {COLORS["button_hover"]};
    color: {COLORS["text_primary"]};
}}

/* =========================================================
   Main chat area
   ========================================================= */

QWidget#chatArea {{
    background-color: {COLORS["main_bg"]};
}}

QScrollArea#chatScroll {{
    background-color: {COLORS["main_bg"]};
    border: none;
}}

QWidget#messagesContainer {{
    background-color: {COLORS["main_bg"]};
}}

/* =========================================================
   Welcome screen
   ========================================================= */

QLabel#welcomeText {{
    background-color: transparent;
    color: {COLORS["text_primary"]};
    font-size: 28px;
    font-weight: 600;
}}

/* =========================================================
   Message layout
   ========================================================= */

QWidget#messageRow {{
    background-color: transparent;
}}

QWidget#userMessageRow {{
    background-color: transparent;
}}

QFrame#userBubble {{
    background-color: {COLORS["user_bubble"]};
    border-radius: 18px;
    border: none;
}}

QFrame#assistantBubble {{
    background-color: transparent;
    border-radius: 0px;
    border: none;
}}

QFrame#systemBubble {{
    background-color: transparent;
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
}}

QLabel#bubbleText {{
    background-color: transparent;
    color: {COLORS["text_primary"]};
    font-size: 14px;
    line-height: 1.7;
    padding: 2px;
}}

QLabel#systemText {{
    background-color: transparent;
    color: {COLORS["text_muted"]};
    font-size: 12px;
    font-style: italic;
}}

QLabel#roleLabel {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    font-size: 12px;
    font-weight: 600;
}}

/* =========================================================
   Model selector bar (top bar)
   ========================================================= */

QWidget#modelBar {{
    background-color: {COLORS["main_bg"]};
}}

QComboBox#modelSelector {{
    background-color: transparent;
    color: {COLORS["text_primary"]};
    border: none;
    border-radius: 6px;
    padding: 4px 24px 4px 8px;
    font-size: 14px;
    font-weight: 600;
    min-width: 120px;
}}

QComboBox#modelSelector:hover {{
    background-color: {COLORS["button_hover"]};
}}

QComboBox#modelSelector::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox#modelSelector::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {COLORS["text_secondary"]};
    width: 0;
    height: 0;
}}

QComboBox#modelSelector QAbstractItemView {{
    background-color: {COLORS["sidebar_bg"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    color: {COLORS["text_primary"]};
    selection-background-color: {COLORS["button_hover"]};
    padding: 4px;
    outline: none;
}}

QPushButton#profileBtn {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    border: none;
    border-radius: 16px;
    font-size: 13px;
    font-weight: 600;
    min-width: 32px;
    min-height: 32px;
    max-width: 32px;
    max-height: 32px;
}}

QPushButton#profileBtn:hover {{
    background-color: {COLORS["button_hover"]};
    color: {COLORS["text_primary"]};
}}

/* =========================================================
   Input bar — centered pill design
   ========================================================= */

QWidget#inputOuter {{
    background-color: {COLORS["main_bg"]};
}}

QWidget#inputPill {{
    background-color: {COLORS["input_bg"]};
    border-radius: 16px;
    border: 1px solid {COLORS["input_border"]};
}}

QWidget#inputPill:focus-within {{
    border-color: {COLORS["border_light"]};
}}

QTextEdit#inputField {{
    background-color: transparent;
    color: {COLORS["text_primary"]};
    border: none;
    border-radius: 0px;
    padding: 10px 4px 10px 4px;
    font-size: 15px;
    selection-background-color: {COLORS["accent"]};
}}

QTextEdit#inputField:focus {{
    border: none;
}}

QPushButton#sendBtn {{
    background-color: {COLORS["text_primary"]};
    color: {COLORS["main_bg"]};
    border: none;
    border-radius: 10px;
    font-size: 14px;
    font-weight: bold;
    min-width: 34px;
    min-height: 34px;
    max-width: 34px;
    max-height: 34px;
}}

QPushButton#sendBtn:hover {{
    background-color: #ffffff;
}}

QPushButton#sendBtn:pressed {{
    background-color: {COLORS["text_secondary"]};
}}

QPushButton#sendBtn:disabled {{
    background-color: {COLORS["send_btn_disabled"]};
    color: {COLORS["text_muted"]};
}}

/* =========================================================
   TTS checkbox
   ========================================================= */

QCheckBox#ttsCheckbox {{
    color: {COLORS["text_secondary"]};
    font-size: 12px;
    spacing: 6px;
    background: transparent;
}}

QCheckBox#ttsCheckbox:hover {{
    color: {COLORS["text_primary"]};
}}

QCheckBox#ttsCheckbox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {COLORS["border_light"]};
    border-radius: 3px;
    background-color: transparent;
}}

QCheckBox#ttsCheckbox::indicator:checked {{
    background-color: {COLORS["accent"]};
    border-color: {COLORS["accent"]};
}}

/* =========================================================
   Image generation window
   ========================================================= */

QWidget#imageArea {{
    background-color: {COLORS["main_bg"]};
}}

QLabel#sectionLabel {{
    color: {COLORS["text_secondary"]};
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
    padding-bottom: 4px;
    background: transparent;
}}

QTextEdit#promptInput, QTextEdit#negPromptInput {{
    background-color: {COLORS["input_bg"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
    padding: 10px 12px;
    font-size: 14px;
}}

QTextEdit#promptInput:focus, QTextEdit#negPromptInput:focus {{
    border-color: {COLORS["border_light"]};
}}

QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS["input_bg"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 13px;
    min-width: 70px;
}}

QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {COLORS["border_light"]};
}}

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: {COLORS["border"]};
    border: none;
    width: 16px;
    border-radius: 3px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {COLORS["border_light"]};
}}

QPushButton#generateBtn {{
    background-color: {COLORS["accent"]};
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: 600;
}}

QPushButton#generateBtn:hover {{
    background-color: {COLORS["accent_hover"]};
}}

QPushButton#generateBtn:disabled {{
    background-color: {COLORS["border"]};
    color: {COLORS["text_muted"]};
}}

QPushButton#saveBtn {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 13px;
}}

QPushButton#saveBtn:hover {{
    background-color: {COLORS["button_hover"]};
    color: {COLORS["text_primary"]};
    border-color: {COLORS["border_light"]};
}}

QPushButton#saveBtn:disabled {{
    color: {COLORS["text_muted"]};
    border-color: {COLORS["border"]};
}}

QLabel#imagePlaceholder {{
    background-color: {COLORS["input_bg"]};
    color: {COLORS["text_muted"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
    font-size: 13px;
}}

/* =========================================================
   Scrollbars — minimal/invisible style
   ========================================================= */

QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
    border-radius: 3px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS["scrollbar_handle"]};
    min-height: 30px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS["border_light"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    margin: 0;
    border-radius: 3px;
}}

QScrollBar::handle:horizontal {{
    background: {COLORS["scrollbar_handle"]};
    min-width: 30px;
    border-radius: 3px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}

/* =========================================================
   QSplitter handle — invisible thin separator
   ========================================================= */

QSplitter::handle {{
    background: {COLORS["border"]};
    width: 1px;
    height: 1px;
}}

/* =========================================================
   Tooltips
   ========================================================= */

QToolTip {{
    background-color: {COLORS["sidebar_bg"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
}}
"""
