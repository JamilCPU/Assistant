"""
Global QSS stylesheet for the ChatGPT-style dark UI.

Usage:
    from frontend.components.style import APP_STYLESHEET
    app.setStyleSheet(APP_STYLESHEET)
"""

# Color palette
COLORS = {
    "sidebar_bg": "#202123",
    "main_bg": "#343541",
    "input_bg": "#40414f",
    "user_bubble": "#40414f",
    "assistant_bubble": "#2d2d30",
    "border": "#4d4d4f",
    "border_light": "#565869",
    "text_primary": "#ececec",
    "text_secondary": "#8e8ea0",
    "text_muted": "#6b6b7b",
    "accent": "#10a37f",          # ChatGPT green
    "accent_hover": "#1abc8f",
    "button_hover": "#2a2b32",
    "button_active": "#343541",
    "scrollbar_bg": "#2a2b32",
    "scrollbar_handle": "#4d4d4f",
    "danger": "#e34040",
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
    line-height: 1.6;
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
    border-right: 1px solid {COLORS["border"]};
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
    padding: 8px 12px;
    border-radius: 6px;
    margin: 1px 8px;
}}

QListWidget#historyList::item:hover {{
    background-color: {COLORS["button_hover"]};
    color: {COLORS["text_primary"]};
}}

QListWidget#historyList::item:selected {{
    background-color: {COLORS["button_active"]};
    color: {COLORS["text_primary"]};
}}

/* Sidebar buttons */
QPushButton#newChatBtn {{
    background-color: transparent;
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 10px 14px;
    text-align: left;
    font-size: 13px;
}}

QPushButton#newChatBtn:hover {{
    background-color: {COLORS["button_hover"]};
    border-color: {COLORS["border_light"]};
}}

QPushButton#newChatBtn:pressed {{
    background-color: {COLORS["button_active"]};
}}

QPushButton#modeBtn {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    border: none;
    border-radius: 6px;
    padding: 10px 14px;
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
    padding: 10px 14px;
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
   Message bubbles
   ========================================================= */

QFrame#userBubble {{
    background-color: {COLORS["user_bubble"]};
    border-radius: 10px;
    border: none;
}}

QFrame#assistantBubble {{
    background-color: {COLORS["assistant_bubble"]};
    border-radius: 10px;
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
    line-height: 1.6;
    padding: 2px;
}}

QLabel#systemText {{
    background-color: transparent;
    color: {COLORS["text_muted"]};
    font-size: 12px;
    font-style: italic;
}}

/* =========================================================
   Model selector bar
   ========================================================= */

QWidget#modelBar {{
    background-color: {COLORS["main_bg"]};
    border-bottom: 1px solid {COLORS["border"]};
}}

QComboBox#modelSelector {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 4px 28px 4px 10px;
    font-size: 13px;
    min-width: 160px;
}}

QComboBox#modelSelector:hover {{
    border-color: {COLORS["border_light"]};
    color: {COLORS["text_primary"]};
}}

QComboBox#modelSelector::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox#modelSelector QAbstractItemView {{
    background-color: {COLORS["sidebar_bg"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    color: {COLORS["text_primary"]};
    selection-background-color: {COLORS["button_hover"]};
    padding: 4px;
}}

/* =========================================================
   Input bar
   ========================================================= */

QWidget#inputBar {{
    background-color: {COLORS["main_bg"]};
    border-top: 1px solid {COLORS["border"]};
    padding: 12px 16px;
}}

QTextEdit#inputField {{
    background-color: {COLORS["input_bg"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 14px;
    selection-background-color: {COLORS["accent"]};
}}

QTextEdit#inputField:focus {{
    border-color: {COLORS["border_light"]};
}}

QPushButton#sendBtn {{
    background-color: {COLORS["accent"]};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 16px;
    font-weight: bold;
    min-width: 38px;
    min-height: 38px;
}}

QPushButton#sendBtn:hover {{
    background-color: {COLORS["accent_hover"]};
}}

QPushButton#sendBtn:pressed {{
    background-color: {COLORS["accent"]};
}}

QPushButton#sendBtn:disabled {{
    background-color: {COLORS["border"]};
    color: {COLORS["text_muted"]};
}}

/* =========================================================
   TTS checkbox
   ========================================================= */

QCheckBox#ttsCheckbox {{
    color: {COLORS["text_secondary"]};
    font-size: 12px;
    spacing: 6px;
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
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding-bottom: 4px;
}}

QTextEdit#promptInput, QTextEdit#negPromptInput {{
    background-color: {COLORS["input_bg"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
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
    border-radius: 6px;
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
    border-radius: 8px;
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
    border-radius: 6px;
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
    background-color: {COLORS["sidebar_bg"]};
    color: {COLORS["text_muted"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    font-size: 13px;
}}

/* =========================================================
   Scrollbars — minimal style
   ========================================================= */

QScrollBar:vertical {{
    background: {COLORS["scrollbar_bg"]};
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
    background: {COLORS["scrollbar_bg"]};
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
   QSplitter handle — invisible
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
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}
"""
