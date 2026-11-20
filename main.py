from prog import Prog

# Init du programme
def main() -> None:
    prog = Prog()
    prog.init_prog()
    prog.run()
    prog.quit_prog()

if __name__ == '__main__':
    main()