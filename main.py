import sys
from PyQt5.QtWidgets import QApplication
from interface import CleanCrowUI


def main():
    # Verificar se o sistema é Windows
    if sys.platform != "win32":
        print("Este software é compatível apenas com Windows.")
        return

    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Estilo moderno

    window = CleanCrowUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()