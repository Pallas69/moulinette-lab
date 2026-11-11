"""Catalogue interne de la Piscine C++ (Modules 00 à 08, 45 exercices)."""

ACCOUNT_HPP = r'''#ifndef __ACCOUNT_H__
#define __ACCOUNT_H__

class Account {
public:
    typedef Account t;
    static int getNbAccounts( void );
    static int getTotalAmount( void );
    static int getNbDeposits( void );
    static int getNbWithdrawals( void );
    static void displayAccountsInfos( void );

    Account( int initial_deposit );
    ~Account( void );

    void makeDeposit( int deposit );
    bool makeWithdrawal( int withdrawal );
    int checkAmount( void ) const;
    void displayStatus( void ) const;

private:
    static int _nbAccounts;
    static int _totalAmount;
    static int _totalNbDeposits;
    static int _totalNbWithdrawals;

    static void _displayTimestamp( void );

    int _accountIndex;
    int _amount;
    int _nbDeposits;
    int _nbWithdrawals;

    Account( void );
};

#endif
'''

ACCOUNT_TESTS_CPP = r'''#include <vector>
#include <algorithm>
#include <functional>
#include "Account.class.hpp"

int main( void ) {
    typedef std::vector<Account::t> accounts_t;
    typedef std::vector<int> ints_t;
    typedef std::pair<accounts_t::iterator, ints_t::iterator> acc_int_t;

    int const amounts[] = { 42, 54, 957, 432, 1234, 0, 754, 16576 };
    size_t const amounts_size( sizeof(amounts) / sizeof(int) );
    accounts_t accounts( amounts, amounts + amounts_size );
    accounts_t::iterator acc_begin = accounts.begin();
    accounts_t::iterator acc_end = accounts.end();

    int const d[] = { 5, 765, 564, 2, 87, 23, 9, 20 };
    size_t const d_size( sizeof(d) / sizeof(int) );
    ints_t deposits( d, d + d_size );
    ints_t::iterator dep_begin = deposits.begin();
    ints_t::iterator dep_end = deposits.end();

    int const w[] = { 321, 34, 657, 4, 76, 275, 657, 7654 };
    size_t const w_size( sizeof(w) / sizeof(int) );
    ints_t withdrawals( w, w + w_size );
    ints_t::iterator wit_begin = withdrawals.begin();
    ints_t::iterator wit_end = withdrawals.end();

    Account::displayAccountsInfos();
    std::for_each( acc_begin, acc_end, std::mem_fun_ref( &Account::displayStatus ) );

    for ( acc_int_t it( acc_begin, dep_begin );
          it.first != acc_end && it.second != dep_end;
          ++(it.first), ++(it.second) ) {
        (*(it.first)).makeDeposit( *(it.second) );
    }

    Account::displayAccountsInfos();
    std::for_each( acc_begin, acc_end, std::mem_fun_ref( &Account::displayStatus ) );

    for ( acc_int_t it( acc_begin, wit_begin );
          it.first != acc_end && it.second != wit_end;
          ++(it.first), ++(it.second) ) {
        (*(it.first)).makeWithdrawal( *(it.second) );
    }

    Account::displayAccountsInfos();
    std::for_each( acc_begin, acc_end, std::mem_fun_ref( &Account::displayStatus ) );

    return 0;
}
'''

ACCOUNT_EXPECTED_LINES = [
    "index:0;amount:42;created",
    "index:1;amount:54;created",
    "index:2;amount:957;created",
    "index:3;amount:432;created",
    "index:4;amount:1234;created",
    "index:5;amount:0;created",
    "index:6;amount:754;created",
    "index:7;amount:16576;created",
    "accounts:8;total:20049;deposits:0;withdrawals:0",
    "index:0;amount:42;deposits:0;withdrawals:0",
    "index:1;amount:54;deposits:0;withdrawals:0",
    "index:2;amount:957;deposits:0;withdrawals:0",
    "index:3;amount:432;deposits:0;withdrawals:0",
    "index:4;amount:1234;deposits:0;withdrawals:0",
    "index:5;amount:0;deposits:0;withdrawals:0",
    "index:6;amount:754;deposits:0;withdrawals:0",
    "index:7;amount:16576;deposits:0;withdrawals:0",
    "index:0;p_amount:42;deposit:5;amount:47;nb_deposits:1",
    "index:1;p_amount:54;deposit:765;amount:819;nb_deposits:1",
    "index:2;p_amount:957;deposit:564;amount:1521;nb_deposits:1",
    "index:3;p_amount:432;deposit:2;amount:434;nb_deposits:1",
    "index:4;p_amount:1234;deposit:87;amount:1321;nb_deposits:1",
    "index:5;p_amount:0;deposit:23;amount:23;nb_deposits:1",
    "index:6;p_amount:754;deposit:9;amount:763;nb_deposits:1",
    "index:7;p_amount:16576;deposit:20;amount:16596;nb_deposits:1",
    "accounts:8;total:21524;deposits:8;withdrawals:0",
    "index:0;amount:47;deposits:1;withdrawals:0",
    "index:1;amount:819;deposits:1;withdrawals:0",
    "index:2;amount:1521;deposits:1;withdrawals:0",
    "index:3;amount:434;deposits:1;withdrawals:0",
    "index:4;amount:1321;deposits:1;withdrawals:0",
    "index:5;amount:23;deposits:1;withdrawals:0",
    "index:6;amount:763;deposits:1;withdrawals:0",
    "index:7;amount:16596;deposits:1;withdrawals:0",
    "index:0;p_amount:47;withdrawal:refused",
    "index:1;p_amount:819;withdrawal:34;amount:785;nb_withdrawals:1",
    "index:2;p_amount:1521;withdrawal:657;amount:864;nb_withdrawals:1",
    "index:3;p_amount:434;withdrawal:4;amount:430;nb_withdrawals:1",
    "index:4;p_amount:1321;withdrawal:76;amount:1245;nb_withdrawals:1",
    "index:5;p_amount:23;withdrawal:refused",
    "index:6;p_amount:763;withdrawal:657;amount:106;nb_withdrawals:1",
    "index:7;p_amount:16596;withdrawal:7654;amount:8942;nb_withdrawals:1",
    "accounts:8;total:12442;deposits:8;withdrawals:6",
    "index:0;amount:47;deposits:1;withdrawals:0",
    "index:1;amount:785;deposits:1;withdrawals:1",
    "index:2;amount:864;deposits:1;withdrawals:1",
    "index:3;amount:430;deposits:1;withdrawals:1",
    "index:4;amount:1245;deposits:1;withdrawals:1",
    "index:5;amount:23;deposits:1;withdrawals:0",
    "index:6;amount:106;deposits:1;withdrawals:1",
    "index:7;amount:8942;deposits:1;withdrawals:1",
]


def _spec(module, ex, title, source, required_files, kind, **extra):
    d = {
        "piscine": "cpp",
        "module": module,
        "exercise": f"{module}/{ex}",
        "title": title,
        "source": source,
        "required_files": tuple(required_files),
        "kind": kind,
        "subject_version": "1.0",
        "allow_stl": module == "cpp08",
        "require_coplien": module in ("cpp02", "cpp03", "cpp04", "cpp05", "cpp06", "cpp07", "cpp08"),
    }
    d.update(extra)
    return d


CPP_EXERCISES = {
    # Module 00 (3 exercices)
    "cpp00/ex00": _spec(
        "cpp00", "ex00", "Megaphone", "megaphone.cpp",
        ("Makefile", "megaphone.cpp"), "makefile_program",
        binary="megaphone",
        cases=[
            ("sans argument", [], b"* LOUD AND UNBEARABLE FEEDBACK NOISE *\n"),
            ("phrase simple", ["shhhhh... I think the students are asleep..."], b"SHHHHH... I THINK THE STUDENTS ARE ASLEEP...\n"),
            ("arguments multiples", ["Damnit", " ! ", "Sorry students, I thought this thing was off."],
             b"DAMNIT ! SORRY STUDENTS, I THOUGHT THIS THING WAS OFF.\n"),
        ],
    ),
    "cpp00/ex01": _spec(
        "cpp00", "ex01", "My Awesome PhoneBook", "Makefile",
        ("Makefile",), "phonebook_program",
        require_cpp_sources=True,
    ),
    "cpp00/ex02": _spec(
        "cpp00", "ex02", "The Job Of Your Dreams", "Account.class.cpp",
        ("Account.class.cpp",), "account_harness",
        support_files={"Account.class.hpp": ACCOUNT_HPP, "tests.cpp": ACCOUNT_TESTS_CPP},
        expected_lines=ACCOUNT_EXPECTED_LINES,
    ),

    # Module 01 (11 exercices)
    "cpp01/ex00": _spec(
        "cpp01", "ex00", "Pony on the Heap / Stack", "Pony.cpp",
        ("Pony.cpp", "Pony.hpp", "main.cpp"), "student_main_and_harness",
        required_tokens=("ponyOnTheHeap", "ponyOnTheStack", "new", "delete"),
    ),
    "cpp01/ex01": _spec(
        "cpp01", "ex01", "Memory Leak (Plumbing problem)", "ex01.cpp",
        ("ex01.cpp",), "harness_only",
        required_tokens=("memoryLeak", "String panther", "delete"),
        harness=r'''#include <iostream>
void memoryLeak();
int main() {
    memoryLeak();
    return 0;
}
''',
        expected_substr=b"String panther",
    ),
    "cpp01/ex02": _spec(
        "cpp01", "ex02", "Plucking some brains", "ZombieEvent.cpp",
        ("Zombie.cpp", "Zombie.hpp", "ZombieEvent.cpp", "ZombieEvent.hpp", "main.cpp"),
        "student_main_and_harness",
        harness=r'''#include "Zombie.hpp"
#include "ZombieEvent.hpp"
int main() {
    ZombieEvent ev;
    ev.setZombieType("runner");
    Zombie *z = ev.newZombie("Foo");
    z->announce();
    delete z;
    ev.randomChump();
    return 0;
}
''',
        expected_substr=b"Braiiiiiiinnnssss...",
    ),
    "cpp01/ex03": _spec(
        "cpp01", "ex03", "Moar brainz!", "ZombieHorde.cpp",
        ("Zombie.cpp", "Zombie.hpp", "ZombieHorde.cpp", "ZombieHorde.hpp", "main.cpp"),
        "student_main_and_harness",
        harness=r'''#include "ZombieHorde.hpp"
int main() {
    ZombieHorde horde(4);
    horde.announce();
    return 0;
}
''',
        expected_substr=b"Braiiiiiiinnnssss...",
        expected_count=(b"Braiiiiiiinnnssss...", 4),
    ),
    "cpp01/ex04": _spec(
        "cpp01", "ex04", "HI THIS IS BRAIN", "ex04.cpp",
        ("ex04.cpp",), "student_main_only",
        required_tokens=("HI THIS IS BRAIN",),
        expected_count=(b"HI THIS IS BRAIN", 2),
    ),
    "cpp01/ex05": _spec(
        "cpp01", "ex05", "HI BRAIN THIS IS HUMAN", "Human.cpp",
        ("Brain.cpp", "Brain.hpp", "Human.cpp", "Human.hpp", "main.cpp"),
        "student_main_and_harness",
        harness=r'''#include <iostream>
#include "Human.hpp"
int main() {
    Human bob;
    std::string a = bob.identify();
    std::string b = bob.getBrain().identify();
    if (a.empty() || a != b || a.find("0x") == std::string::npos) return 1;
    std::cout << a << "\n" << b << std::endl;
    return 0;
}
''',
        expected_substr=b"0x",
    ),
    "cpp01/ex06": _spec(
        "cpp01", "ex06", "Unnecessary violence", "Weapon.cpp",
        ("Weapon.cpp", "Weapon.hpp", "HumanA.cpp", "HumanA.hpp", "HumanB.cpp", "HumanB.hpp", "main.cpp"),
        "student_main_and_harness",
        harness=r'''#include "Weapon.hpp"
#include "HumanA.hpp"
#include "HumanB.hpp"
int main() {
    {
        Weapon club = Weapon("crude spiked club");
        HumanA bob("Bob", club);
        bob.attack();
        club.setType("some other type of club");
        bob.attack();
    }
    {
        Weapon club = Weapon("crude spiked club");
        HumanB jim("Jim");
        jim.setWeapon(club);
        jim.attack();
        club.setType("some other type of club");
        jim.attack();
    }
    return 0;
}
''',
        expected_exact=(
            b"Bob attacks with his crude spiked club\n"
            b"Bob attacks with his some other type of club\n"
            b"Jim attacks with his crude spiked club\n"
            b"Jim attacks with his some other type of club\n"
        ),
    ),
    "cpp01/ex07": _spec(
        "cpp01", "ex07", "Sed is for losers", "Makefile",
        ("Makefile",), "replace_program",
        binary="replace",
        require_cpp_sources=True,
    ),
    "cpp01/ex08": _spec(
        "cpp01", "ex08", "I ain't heard of no fancy switches", "Human.cpp",
        ("Human.cpp", "Human.hpp", "main.cpp"), "student_main_and_harness",
        forbidden_tokens=("switch",),
        harness=r'''#include "Human.hpp"
int main() {
    Human h;
    h.action("meleeAttack", "targetA");
    h.action("rangedAttack", "targetB");
    h.action("intimidatingShout", "targetC");
    return 0;
}
''',
        expected_substr=b"targetA",
    ),
    "cpp01/ex09": _spec(
        "cpp01", "ex09", "Over logging", "Logger.cpp",
        ("Logger.cpp", "Logger.hpp", "main.cpp"), "student_main_and_harness",
        harness=r'''#include "Logger.hpp"
int main() {
    Logger lg("test_log_output.txt");
    lg.log("logToConsole", "Hello console");
    lg.log("logToFile", "Hello file");
    return 0;
}
''',
        expected_substr=b"Hello console",
        expected_file=("test_log_output.txt", b"Hello file"),
    ),
    "cpp01/ex10": _spec(
        "cpp01", "ex10", "Cat o' nine tails", "Makefile",
        ("Makefile",), "cato9tails_program",
        binary="cato9tails",
        require_cpp_sources=True,
    ),

    # Module 02 (4 exercices)
    "cpp02/ex00": _spec(
        "cpp02", "ex00", "My First Canonical Class", "Fixed.cpp",
        (), "fixed_harness",
        flexible_pairs=(("Fixed.class.hpp", "Fixed.class.cpp"), ("Fixed.hpp", "Fixed.cpp")),
        harness=r'''#include <iostream>
#include "__FIXED_HEADER__"
int main(void) {
    Fixed a;
    Fixed b(a);
    Fixed c;
    c = b;
    std::cout << a.getRawBits() << std::endl;
    std::cout << b.getRawBits() << std::endl;
    std::cout << c.getRawBits() << std::endl;
    return 0;
}
''',
        expected_substr=b"getRawBits member function called\n0\n",
    ),
    "cpp02/ex01": _spec(
        "cpp02", "ex01", "Towards a more useful fixed point class", "Fixed.cpp",
        (), "fixed_harness",
        flexible_pairs=(("Fixed.class.hpp", "Fixed.class.cpp"), ("Fixed.hpp", "Fixed.cpp")),
        harness=r'''#include <iostream>
#include "__FIXED_HEADER__"
int main(void) {
    Fixed a;
    Fixed const b(10);
    Fixed const c(42.42f);
    Fixed const d(b);
    a = Fixed(1234.4321f);
    std::cout << "a is " << a << std::endl;
    std::cout << "b is " << b << std::endl;
    std::cout << "c is " << c << std::endl;
    std::cout << "d is " << d << std::endl;
    std::cout << "a is " << a.toInt() << " as integer" << std::endl;
    std::cout << "b is " << b.toInt() << " as integer" << std::endl;
    std::cout << "c is " << c.toInt() << " as integer" << std::endl;
    std::cout << "d is " << d.toInt() << " as integer" << std::endl;
    return 0;
}
''',
        expected_substr=b"a is 1234 as integer\nb is 10 as integer\nc is 42 as integer\nd is 10 as integer\n",
    ),
    "cpp02/ex02": _spec(
        "cpp02", "ex02", "Now we're talking", "Fixed.cpp",
        (), "fixed_harness",
        flexible_pairs=(("Fixed.class.hpp", "Fixed.class.cpp"), ("Fixed.hpp", "Fixed.cpp")),
        harness=r'''#include <iostream>
#include "__FIXED_HEADER__"
int main(void) {
    Fixed a;
    Fixed const b(Fixed(5.05f) * Fixed(2));
    std::cout << a << std::endl;
    std::cout << ++a << std::endl;
    std::cout << a << std::endl;
    std::cout << a++ << std::endl;
    std::cout << a << std::endl;
    std::cout << b << std::endl;
    std::cout << Fixed::max(a, b) << std::endl;
    std::cout << Fixed::min(a, b) << std::endl;
    std::cout << (b > a) << ":" << (a < b) << ":" << (a == a) << ":" << (a != b) << std::endl;
    return 0;
}
''',
        expected_substr=b"1:1:1:1\n",
    ),
    "cpp02/ex03": _spec(
        "cpp02", "ex03", "Fixed point expressions", "Makefile",
        ("Makefile",), "makefile_program",
        binary="eval_expr",
        require_cpp_sources=True,
        cases=[
            ("addition simple", ["1 + 1"], b"2\n"),
            ("expression avec parenthèses", ["( 2 + 3 ) * 4"], b"20\n"),
        ],
    ),

    # Module 03 (5 exercices)
    "cpp03/ex00": _spec(
        "cpp03", "ex00", "Aaaaand... OPEN!", "FragTrap.cpp",
        ("FragTrap.cpp", "FragTrap.hpp", "main.cpp"), "student_main_and_harness",
        harness=r'''#include "FragTrap.hpp"
int main() {
    FragTrap ft("CL4P-TP");
    ft.rangedAttack("Bandit");
    ft.meleeAttack("Psycho");
    ft.takeDamage(30);
    ft.beRepaired(20);
    ft.vaulthunter_dot_exe("Boss");
    return 0;
}
''',
        expected_substr=b"FR4G-TP",
    ),
    "cpp03/ex01": _spec(
        "cpp03", "ex01", "Serena, my love!", "ScavTrap.cpp",
        ("FragTrap.cpp", "FragTrap.hpp", "ScavTrap.cpp", "ScavTrap.hpp", "main.cpp"),
        "student_main_and_harness",
        harness=r'''#include "FragTrap.hpp"
#include "ScavTrap.hpp"
int main() {
    FragTrap ft("Frag");
    ScavTrap st("Scav");
    ft.rangedAttack("Target");
    st.meleeAttack("Target");
    st.challengeNewcomer("VaultHunter");
    return 0;
}
''',
        expected_substr=b"Scav",
    ),
    "cpp03/ex02": _spec(
        "cpp03", "ex02", "Repetitive work", "ClapTrap.cpp",
        ("ClapTrap.cpp", "ClapTrap.hpp", "FragTrap.cpp", "FragTrap.hpp", "ScavTrap.cpp", "ScavTrap.hpp", "main.cpp"),
        "student_main_and_harness",
        harness=r'''#include "ClapTrap.hpp"
#include "FragTrap.hpp"
#include "ScavTrap.hpp"
int main() {
    FragTrap ft("Frag");
    ScavTrap st("Scav");
    ClapTrap &base1 = ft;
    ClapTrap &base2 = st;
    base1.takeDamage(20);
    base2.beRepaired(10);
    return 0;
}
''',
        expected_substr=b"Frag",
    ),
    "cpp03/ex03": _spec(
        "cpp03", "ex03", "Now it's weird!", "NinjaTrap.cpp",
        ("ClapTrap.cpp", "ClapTrap.hpp", "FragTrap.cpp", "FragTrap.hpp",
         "ScavTrap.cpp", "ScavTrap.hpp", "NinjaTrap.cpp", "NinjaTrap.hpp", "main.cpp"),
        "student_main_and_harness",
        harness=r'''#include "ClapTrap.hpp"
#include "FragTrap.hpp"
#include "ScavTrap.hpp"
#include "NinjaTrap.hpp"
int main() {
    FragTrap ft("Frag");
    ScavTrap st("Scav");
    ClapTrap ct("Clap");
    NinjaTrap nt("Ninja");
    nt.ninjaShoebox(ft);
    nt.ninjaShoebox(st);
    nt.ninjaShoebox(ct);
    nt.ninjaShoebox(nt);
    return 0;
}
''',
        expected_substr=b"Ninja",
    ),
    "cpp03/ex04": _spec(
        "cpp03", "ex04", "SuperTrap", "SuperTrap.cpp",
        ("ClapTrap.cpp", "ClapTrap.hpp", "FragTrap.cpp", "FragTrap.hpp",
         "ScavTrap.cpp", "ScavTrap.hpp", "NinjaTrap.cpp", "NinjaTrap.hpp",
         "SuperTrap.cpp", "SuperTrap.hpp", "main.cpp"),
        "student_main_and_harness",
        harness=r'''#include "SuperTrap.hpp"
int main() {
    SuperTrap sup("Super");
    FragTrap ft("Frag");
    sup.rangedAttack("Enemy");
    sup.meleeAttack("Enemy");
    sup.vaulthunter_dot_exe("Enemy");
    sup.ninjaShoebox(ft);
    return 0;
}
''',
        expected_substr=b"Super",
    ),

    # Module 04 (5 exercices)
    "cpp04/ex00": _spec(
        "cpp04", "ex00", "Polymorphism, or When the boilerplate-code...", "Sorcerer.cpp",
        ("Sorcerer.cpp", "Sorcerer.hpp", "Victim.cpp", "Victim.hpp", "Peon.cpp", "Peon.hpp", "main.cpp"),
        "student_main_and_harness",
        harness=r'''#include <iostream>
#include "Sorcerer.hpp"
#include "Victim.hpp"
#include "Peon.hpp"
int main() {
    Sorcerer robert("Robert", "the Magnificent");
    Victim jim("Jimmy");
    Peon joe("Joe");
    std::cout << robert << jim << joe;
    robert.polymorph(jim);
    robert.polymorph(joe);
    return 0;
}
''',
        expected_exact=(
            b"Robert, the Magnificent, is born!\n"
            b"Some random victim called Jimmy just appeared!\n"
            b"Some random victim called Joe just appeared!\n"
            b"Zog zog.\n"
            b"I am Robert, the Magnificent, and I like ponies!\n"
            b"I'm Jimmy and I like otters!\n"
            b"I'm Joe and I like otters!\n"
            b"Jimmy has been turned into a cute little sheep!\n"
            b"Joe has been turned into a pink pony!\n"
            b"Bleuark...\n"
            b"Victim Joe just died for no apparent reason!\n"
            b"Victim Jimmy just died for no apparent reason!\n"
            b"Robert, the Magnificent, is dead. Consequences will never be the same!\n"
        ),
    ),
    "cpp04/ex01": _spec(
        "cpp04", "ex01", "I don't want to set the world on fire", "Character.cpp",
        ("AWeapon.cpp", "AWeapon.hpp", "PlasmaRifle.cpp", "PlasmaRifle.hpp",
         "PowerFist.cpp", "PowerFist.hpp", "Enemy.cpp", "Enemy.hpp",
         "SuperMutant.cpp", "SuperMutant.hpp", "RadScorpion.cpp", "RadScorpion.hpp",
         "Character.cpp", "Character.hpp", "main.cpp"),
        "student_main_and_harness",
        harness=r'''#include <iostream>
#include "Character.hpp"
#include "RadScorpion.hpp"
#include "PlasmaRifle.hpp"
#include "PowerFist.hpp"
int main() {
    Character* me = new Character("me");
    std::cout << *me;
    Enemy* b = new RadScorpion();
    AWeapon* pr = new PlasmaRifle();
    AWeapon* pf = new PowerFist();
    me->equip(pr);
    std::cout << *me;
    me->equip(pf);
    me->attack(b);
    std::cout << *me;
    me->equip(pr);
    std::cout << *me;
    me->attack(b);
    std::cout << *me;
    me->attack(b);
    std::cout << *me;
    delete me;
    delete pr;
    delete pf;
    return 0;
}
''',
        expected_exact=(
            b"me has 40 AP and is unarmed\n"
            b"* click click click *\n"
            b"me has 40 AP and wields a Plasma Rifle\n"
            b"me attacks RadScorpion with a Power Fist\n"
            b"* pschhh... SBAM! *\n"
            b"me has 32 AP and wields a Power Fist\n"
            b"me has 32 AP and wields a Plasma Rifle\n"
            b"me attacks RadScorpion with a Plasma Rifle\n"
            b"* piouuu piouuu piouuu *\n"
            b"me has 27 AP and wields a Plasma Rifle\n"
            b"me attacks RadScorpion with a Plasma Rifle\n"
            b"* piouuu piouuu piouuu *\n"
            b"* SPROTCH *\n"
            b"me has 22 AP and wields a Plasma Rifle\n"
        ),
    ),
    "cpp04/ex02": _spec(
        "cpp04", "ex02", "This code is unclean. PURIFY IT!", "Squad.cpp",
        ("ISquad.hpp", "ISpaceMarine.hpp", "Squad.cpp", "Squad.hpp",
         "TacticalMarine.cpp", "TacticalMarine.hpp", "AssaultTerminator.cpp", "AssaultTerminator.hpp", "main.cpp"),
        "student_main_and_harness",
        harness=r'''#include "ISquad.hpp"
#include "ISpaceMarine.hpp"
#include "Squad.hpp"
#include "TacticalMarine.hpp"
#include "AssaultTerminator.hpp"
int main() {
    ISpaceMarine* bob = new TacticalMarine;
    ISpaceMarine* jim = new AssaultTerminator;
    ISquad* vlc = new Squad;
    vlc->push(bob);
    vlc->push(jim);
    for (int i = 0; i < vlc->getCount(); ++i) {
        ISpaceMarine* cur = vlc->getUnit(i);
        cur->battleCry();
        cur->rangedAttack();
        cur->meleeAttack();
    }
    delete vlc;
    return 0;
}
''',
        expected_exact=(
            b"Tactical Marine ready for battle!\n"
            b"* teleports from space *\n"
            b"For the holy PLOT!\n"
            b"* attacks with a bolter *\n"
            b"* attacks with a chainsword *\n"
            b"This code is unclean. PURIFY IT!\n"
            b"* does nothing *\n"
            b"* attacks with chainfists *\n"
            b"Aaargh...\n"
            b"I'll be back...\n"
        ),
    ),
    "cpp04/ex03": _spec(
        "cpp04", "ex03", "Bocal Fantasy", "MateriaSource.cpp",
        ("AMateria.cpp", "AMateria.hpp", "Ice.cpp", "Ice.hpp", "Cure.cpp", "Cure.hpp",
         "ICharacter.hpp", "Character.cpp", "Character.hpp", "IMateriaSource.hpp",
         "MateriaSource.cpp", "MateriaSource.hpp", "main.cpp"),
        "student_main_and_harness",
        harness=r'''#include "IMateriaSource.hpp"
#include "MateriaSource.hpp"
#include "Ice.hpp"
#include "Cure.hpp"
#include "ICharacter.hpp"
#include "Character.hpp"
int main() {
    IMateriaSource* src = new MateriaSource();
    src->learnMateria(new Ice());
    src->learnMateria(new Cure());
    ICharacter* me = new Character("me");
    AMateria* tmp;
    tmp = src->createMateria("ice");
    me->equip(tmp);
    tmp = src->createMateria("cure");
    me->equip(tmp);
    ICharacter* bob = new Character("bob");
    me->use(0, *bob);
    me->use(1, *bob);
    delete bob;
    delete me;
    delete src;
    return 0;
}
''',
        expected_exact=(
            b"* shoots an ice bolt at bob *\n"
            b"* heals bob's wounds *\n"
        ),
    ),
    "cpp04/ex04": _spec(
        "cpp04", "ex04", "Mining Barge", "MiningBarge.cpp",
        ("IMiningLaser.hpp", "IAsteroid.hpp", "DeepCoreMiner.cpp", "DeepCoreMiner.hpp",
         "StripMiner.cpp", "StripMiner.hpp", "AsteroKreog.cpp", "AsteroKreog.hpp",
         "KoalaSteroid.cpp", "KoalaSteroid.hpp", "MiningBarge.cpp", "MiningBarge.hpp", "main.cpp"),
        "student_main_and_harness",
        forbidden_tokens=("typeid", "dynamic_cast"),
        harness=r'''#include "MiningBarge.hpp"
#include "DeepCoreMiner.hpp"
#include "StripMiner.hpp"
#include "AsteroKreog.hpp"
#include "KoalaSteroid.hpp"
int main() {
    MiningBarge barge;
    DeepCoreMiner dcm;
    StripMiner sm;
    AsteroKreog ak;
    KoalaSteroid ks;
    barge.equip(&dcm);
    barge.equip(&sm);
    barge.mine(&ak);
    barge.mine(&ks);
    return 0;
}
''',
        expected_exact=(
            b"* mining deep... got Flavium! *\n"
            b"* strip mining... got Krull! *\n"
            b"* mining deep... got Tartarite! *\n"
            b"* strip mining... got Meium! *\n"
        ),
        normalize_spaces=True,
    ),

    # Module 05 (6 exercices)
    "cpp05/ex00": _spec(
        "cpp05", "ex00", "Mommy, when I grow up, I want to be a bureaucrat!", "Bureaucrat.cpp",
        ("Bureaucrat.cpp", "Bureaucrat.hpp", "main.cpp"), "student_main_and_harness",
        harness=r'''#include <iostream>
#include "Bureaucrat.hpp"
int main() {
    Bureaucrat b("Hermes", 2);
    std::cout << b;
    b.incrementGrade();
    std::cout << b;
    try { b.incrementGrade(); } catch (std::exception &e) { std::cout << "HIGH_OK\n"; }
    try { Bureaucrat low("Low", 151); } catch (std::exception &e) { std::cout << "LOW_OK\n"; }
    return 0;
}
''',
        expected_substr=b"Hermes, bureaucrat grade 1.\nHIGH_OK\nLOW_OK\n",
    ),
    "cpp05/ex01": _spec(
        "cpp05", "ex01", "Form up, maggots!", "Form.cpp",
        ("Bureaucrat.cpp", "Bureaucrat.hpp", "Form.cpp", "Form.hpp", "main.cpp"),
        "student_main_and_harness",
        harness=r'''#include <iostream>
#include "Bureaucrat.hpp"
#include "Form.hpp"
int main() {
    Bureaucrat b("Hermes", 10);
    Form f("Tax28B", 20, 10);
    b.signForm(f);
    std::cout << (f.getSigned() ? "SIGNED_OK" : "NO") << std::endl;
    return 0;
}
''',
        expected_substr=b"SIGNED_OK\n",
    ),
    "cpp05/ex02": _spec(
        "cpp05", "ex02", "No, you need form 28B, not 28C...", "PresidentialPardonForm.cpp",
        ("Bureaucrat.cpp", "Bureaucrat.hpp", "Form.cpp", "Form.hpp",
         "ShrubberyCreationForm.cpp", "ShrubberyCreationForm.hpp",
         "RobotomyRequestForm.cpp", "RobotomyRequestForm.hpp",
         "PresidentialPardonForm.cpp", "PresidentialPardonForm.hpp", "main.cpp"),
        "student_main_and_harness",
        harness=r'''#include <iostream>
#include "Bureaucrat.hpp"
#include "ShrubberyCreationForm.hpp"
#include "RobotomyRequestForm.hpp"
#include "PresidentialPardonForm.hpp"
int main() {
    Bureaucrat boss("Boss", 1);
    ShrubberyCreationForm s("garden");
    RobotomyRequestForm r("Bender");
    PresidentialPardonForm p("Arthur");
    boss.signForm(s);
    boss.executeForm(s);
    boss.signForm(r);
    boss.executeForm(r);
    boss.signForm(p);
    boss.executeForm(p);
    return 0;
}
''',
        expected_substr=b"Zafod Beeblebrox",
        expected_file=("garden_shrubbery", b""),
    ),
    "cpp05/ex03": _spec(
        "cpp05", "ex03", "At least this beats coffee-making", "Intern.cpp",
        ("Bureaucrat.cpp", "Bureaucrat.hpp", "Form.cpp", "Form.hpp",
         "ShrubberyCreationForm.cpp", "ShrubberyCreationForm.hpp",
         "RobotomyRequestForm.cpp", "RobotomyRequestForm.hpp",
         "PresidentialPardonForm.cpp", "PresidentialPardonForm.hpp",
         "Intern.cpp", "Intern.hpp", "main.cpp"),
        "student_main_and_harness",
        harness=r'''#include <iostream>
#include "Bureaucrat.hpp"
#include "Intern.hpp"
int main() {
    Intern someRandomIntern;
    Bureaucrat boss("Boss", 1);
    Form* rrf = someRandomIntern.makeForm("presidential pardon", "Bender");
    if (!rrf) return 1;
    boss.signForm(*rrf);
    boss.executeForm(*rrf);
    delete rrf;
    return 0;
}
''',
        expected_substr=b"Zafod Beeblebrox",
    ),
    "cpp05/ex04": _spec(
        "cpp05", "ex04", "Well, maybe coffee-making wasn't so bad", "OfficeBlock.cpp",
        ("Bureaucrat.cpp", "Bureaucrat.hpp", "Form.cpp", "Form.hpp",
         "ShrubberyCreationForm.cpp", "ShrubberyCreationForm.hpp",
         "RobotomyRequestForm.cpp", "RobotomyRequestForm.hpp",
         "PresidentialPardonForm.cpp", "PresidentialPardonForm.hpp",
         "Intern.cpp", "Intern.hpp", "OfficeBlock.cpp", "OfficeBlock.hpp", "main.cpp"),
        "student_main_and_harness",
        harness=r'''#include "OfficeBlock.hpp"
int main() {
    Intern idiotOne;
    Bureaucrat hermes("Hermes Conrad", 1);
    Bureaucrat bob("Bobby Bobson", 1);
    OfficeBlock ob;
    ob.setIntern(idiotOne);
    ob.setSigner(bob);
    ob.setExecutor(hermes);
    ob.doBureaucracy("presidential pardon", "Pigley");
    return 0;
}
''',
        expected_substr=b"Zafod Beeblebrox",
    ),
    "cpp05/ex05": _spec(
        "cpp05", "ex05", "Endless red-tape", "CentralBureaucracy.cpp",
        ("Bureaucrat.cpp", "Bureaucrat.hpp", "Form.cpp", "Form.hpp",
         "ShrubberyCreationForm.cpp", "ShrubberyCreationForm.hpp",
         "RobotomyRequestForm.cpp", "RobotomyRequestForm.hpp",
         "PresidentialPardonForm.cpp", "PresidentialPardonForm.hpp",
         "Intern.cpp", "Intern.hpp", "OfficeBlock.cpp", "OfficeBlock.hpp",
         "CentralBureaucracy.cpp", "CentralBureaucracy.hpp", "main.cpp"),
        "student_main_and_harness",
        harness=r'''#include "CentralBureaucracy.hpp"
int main() {
    CentralBureaucracy cb;
    Bureaucrat b1("Hermes", 1);
    Bureaucrat b2("Bob", 1);
    cb.feed(b1);
    cb.feed(b2);
    cb.queueUp("Arthur");
    cb.doBureaucracy();
    return 0;
}
''',
        expected_substr=b"Arthur",
    ),

    # Module 06 (3 exercices)
    "cpp06/ex00": _spec(
        "cpp06", "ex00", "Scalar conversion", "Makefile",
        ("Makefile",), "makefile_program",
        binary="convert",
        require_cpp_sources=True,
        cases=[
            ("zéro", ["0"], b"char: Non displayable\nint: 0\nfloat: 0.0f\ndouble: 0.0\n"),
            ("nan", ["nan"], b"char: impossible\nint: impossible\nfloat: nanf\ndouble: nan\n"),
            ("flottant 42.0f", ["42.0f"], b"char: '*'\nint: 42\nfloat: 42.0f\ndouble: 42.0\n"),
        ],
    ),
    "cpp06/ex01": _spec(
        "cpp06", "ex01", "Serialization", "Makefile",
        ("Makefile",), "makefile_and_harness",
        require_cpp_sources=True,
        required_tokens=("serialize", "deserialize", "Data"),
    ),
    "cpp06/ex02": _spec(
        "cpp06", "ex02", "Identify real type", "Makefile",
        ("Makefile",), "makefile_and_harness",
        require_cpp_sources=True,
        forbidden_tokens=("typeid", "<typeinfo>"),
        required_tokens=("identify_from_pointer", "identify_from_reference"),
    ),

    # Module 07 (3 exercices)
    "cpp07/ex00": _spec(
        "cpp07", "ex00", "A few functions", "whatever.cpp",
        ("Makefile", "whatever.cpp"), "makefile_and_harness",
        required_tokens=("template", "swap", "min", "max"),
        expected_substr=b"a = 3, b = 2\nmin( a, b ) = 2\nmax( a, b ) = 3\n",
    ),
    "cpp07/ex01": _spec(
        "cpp07", "ex01", "Iter", "iter.cpp",
        ("Makefile", "iter.cpp"), "makefile_and_harness",
        required_tokens=("template", "iter"),
    ),
    "cpp07/ex02": _spec(
        "cpp07", "ex02", "Array", "Array.hpp",
        ("Makefile", "Array.hpp", "main.cpp"), "student_main_and_harness",
        harness=r'''#include <iostream>
#include "Array.hpp"
int main() {
    Array<int> empty;
    if (empty.size() != 0) return 1;
    Array<int> arr(4);
    for (unsigned int i = 0; i < arr.size(); ++i) arr[i] = (int)(i * 10);
    Array<int> copy(arr);
    arr[0] = 99;
    if (copy[0] != 0 || copy[3] != 30) return 2;
    try {
        std::cout << arr[42] << std::endl;
        return 3;
    } catch (std::exception &e) {
        std::cout << "ARRAY_OK" << std::endl;
    }
    return 0;
}
''',
        expected_substr=b"ARRAY_OK\n",
    ),

    # Module 08 (5 exercices — STL autorisée)
    "cpp08/ex00": _spec(
        "cpp08", "ex00", "Easy find", "easyfind.hpp",
        ("easyfind.hpp", "main.cpp"), "student_main_and_harness",
        harness=r'''#include <iostream>
#include <vector>
#include <list>
#include "easyfind.hpp"
int main() {
    std::vector<int> v;
    v.push_back(10); v.push_back(20); v.push_back(42);
    std::vector<int>::iterator it = easyfind(v, 42);
    if (*it != 42) return 1;
    try {
        easyfind(v, 999);
    } catch (std::exception &e) {
        std::cout << "EASYFIND_OK" << std::endl;
        return 0;
    }
    std::cout << "EASYFIND_OK" << std::endl;
    return 0;
}
''',
        expected_substr=b"EASYFIND_OK\n",
    ),
    "cpp08/ex01": _spec(
        "cpp08", "ex01", "Span", "span.cpp",
        ("span.cpp", "span.hpp", "main.cpp"), "student_main_and_harness",
        harness=r'''#include <iostream>
#include "span.hpp"
int main() {
    Span sp = Span(5);
    sp.addNumber(5);
    sp.addNumber(3);
    sp.addNumber(17);
    sp.addNumber(9);
    sp.addNumber(11);
    std::cout << sp.shortestSpan() << std::endl;
    std::cout << sp.longestSpan() << std::endl;
    try { sp.addNumber(42); return 1; } catch (std::exception &e) {}
    return 0;
}
''',
        expected_exact=b"2\n14\n",
    ),
    "cpp08/ex02": _spec(
        "cpp08", "ex02", "Mutated abomination", "mutantstack.hpp",
        ("mutantstack.cpp", "mutantstack.hpp", "main.cpp"), "student_main_and_harness",
        harness=r'''#include <iostream>
#include "mutantstack.hpp"
int main() {
    MutantStack<int> mstack;
    mstack.push(5);
    mstack.push(17);
    std::cout << mstack.top() << std::endl;
    mstack.pop();
    std::cout << mstack.size() << std::endl;
    mstack.push(3);
    mstack.push(5);
    mstack.push(737);
    mstack.push(0);
    MutantStack<int>::iterator it = mstack.begin();
    MutantStack<int>::iterator ite = mstack.end();
    ++it;
    --it;
    while (it != ite) {
        std::cout << *it << std::endl;
        ++it;
    }
    std::stack<int> s(mstack);
    return 0;
}
''',
        expected_exact=b"17\n1\n5\n3\n5\n737\n0\n",
    ),
    "cpp08/ex03": _spec(
        "cpp08", "ex03", "Open your mind", "Makefile",
        ("Makefile", "main.cpp"), "mindopen_program",
        require_cpp_sources=True,
    ),
    "cpp08/ex04": _spec(
        "cpp08", "ex04", "Polite numbers (Reverse Polish)", "Makefile",
        ("Makefile", "main.cpp"), "rpn_program",
        require_cpp_sources=True,
    ),
}
