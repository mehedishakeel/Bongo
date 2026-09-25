/*
 *  OpenBangla Keyboard
 *  Copyright (C) 2016 Muhammad Mominul Huque <mominul2082@gmail.com>
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <QApplication>
#include <QMessageBox>
#include "TopBar.h"
#include "SingleInstance.h"

int main(int argc, char *argv[]) {
  QApplication app(argc, argv);
  app.setApplicationName("Bongo");
  app.setApplicationVersion(PROJECT_VERSION);
  QApplication::setStyle("Fusion");
  app.setStyleSheet(R"(
    QDialog { background: #f4f7f8; color: #17323a; }
    QGroupBox {
      background: #ffffff; border: 1px solid #dbe4ea; border-radius: 10px;
      margin-top: 12px; padding: 14px 10px 10px 10px; font-weight: 600;
    }
    QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; color: #24515c; }
    QPushButton {
      background: #e8f1f3; color: #17323a; border: 1px solid #ccdce0;
      border-radius: 7px; padding: 6px 12px; min-height: 20px;
    }
    QPushButton:hover { background: #d8f2f5; border-color: #62c7d5; }
    QPushButton:pressed, QPushButton:checked { background: #28b9ce; color: #ffffff; border-color: #159bae; }
    QComboBox, QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox {
      background: #ffffff; color: #17323a; border: 1px solid #cbd9dd;
      border-radius: 6px; padding: 5px 7px; selection-background-color: #28b9ce;
    }
    QComboBox:hover, QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus { border-color: #28b9ce; }
    QCheckBox, QRadioButton, QLabel { color: #17323a; }
    QTabWidget::pane { border: 1px solid #dbe4ea; border-radius: 8px; background: #ffffff; }
    QTabBar::tab { background: #e8eef0; padding: 7px 14px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
    QTabBar::tab:selected { background: #28b9ce; color: #ffffff; }
    QMenu { background: #ffffff; color: #17323a; border: 1px solid #dbe4ea; padding: 5px; }
    QMenu::item { padding: 7px 24px 7px 10px; border-radius: 5px; }
    QMenu::item:selected { background: #d8f2f5; }
  )");

  // Prevent many instances of the app to be launched
  QString name = "org.bongo.keyboard";
  SingleInstance instance;
  if (instance.hasPrevious(name)) {
    QMessageBox msgBox(QMessageBox::Information,
                       "Bongo",
                       "Bongo is already running on this system and\nrunning more than one instance is not allowed.",
                       QMessageBox::Ok);
    msgBox.exec();
    return 0;
  }

  instance.listen(name);

  TopBar w;
  w.show();
  return app.exec();
}
