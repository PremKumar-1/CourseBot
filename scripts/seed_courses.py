"""
Seed the CourseBot database with 40-60 sample courses for demos and testing.
Run from project root: python -m scripts.seed_courses
"""
from pathlib import Path
import sys

# Allow importing app from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db

COURSES = [
    {"course_code": "MATH101", "title": "Calculus I", "description": "Limits, derivatives, and applications. Introduction to integration.", "credits": 1, "department": "MATH", "prerequisites": [], "professor": "Sutthirut Charoenphon"},
    {"course_code": "MATH102", "title": "Calculus II", "description": "Techniques of integration, sequences and series, parametric equations.", "credits": 1, "department": "MATH", "prerequisites": ["MATH101"], "professor": "Sutthirut Charoenphon"},
    {"course_code": "MATH201", "title": "Linear Algebra", "description": "Vectors, matrices, eigenvalues, and linear transformations.", "credits": 1, "department": "MATH", "prerequisites": ["MATH101"], "professor": "Suman Balasubramanian"},
    {"course_code": "MATH202", "title": "Discrete Mathematics", "description": "Logic, sets, proofs, combinatorics, and graph theory.", "credits": 1, "department": "MATH", "prerequisites": ["MATH101"], "professor": "Scott Hyatt"},
    {"course_code": "MATH301", "title": "Probability and Statistics", "description": "Probability theory, random variables, estimation, and hypothesis testing.", "credits": 1, "department": "MATH", "prerequisites": ["MATH102"], "professor": "Zhixin Wu"},
    {"course_code": "CS101", "title": "Introduction to Computer Science", "description": "Programming fundamentals, algorithms, and problem solving using a high-level language.", "credits": 1, "department": "CS", "prerequisites": [], "professor": "Gloria Townsend"},
    {"course_code": "CS102", "title": "Data Structures", "description": "Arrays, linked lists, stacks, queues, trees, and hash tables.", "credits": 1, "department": "CS", "prerequisites": ["CS101"], "professor": "Paul Bible"},
    {"course_code": "CS201", "title": "Computer Systems", "description": "Machine representation, assembly, memory hierarchy, and system-level programming.", "credits": 1, "department": "CS", "prerequisites": ["CS102"], "professor": "Scott Thede"},
    {"course_code": "CS202", "title": "Foundations of Computing", "description": "Automata, formal languages, computability, and complexity.", "credits": 1, "department": "CS", "prerequisites": ["CS102", "MATH202"], "professor": "Chad Byers"},
    {"course_code": "CS301", "title": "Algorithms", "description": "Design and analysis of algorithms, sorting, searching, and graph algorithms.", "credits": 1, "department": "CS", "prerequisites": ["CS102", "MATH202"], "professor": "Mehmet Gulum"},
    {"course_code": "CS302", "title": "Programming Languages", "description": "Syntax, semantics, type systems, and language implementation.", "credits": 1, "department": "CS", "prerequisites": ["CS201", "CS202"], "professor": "Brian Howard"},
    {"course_code": "CS303", "title": "Web Programming", "description": "HTML, CSS, JavaScript, and server-side development.", "credits": 1, "department": "CS", "prerequisites": ["CS102"], "professor": "Mehmet Gulum"},
    {"course_code": "CS401", "title": "Database Systems", "description": "Relational model, SQL, normalization, and transaction processing.", "credits": 1, "department": "CS", "prerequisites": ["CS102", "MATH202"], "professor": "Paul Bible"},
    {"course_code": "CS402", "title": "Machine Learning", "description": "Supervised and unsupervised learning, neural networks, and evaluation.", "credits": 1, "department": "CS", "prerequisites": ["CS301", "MATH201", "MATH301"], "professor": "Allana Johnson"},
    {"course_code": "CS403", "title": "Software Engineering", "description": "Requirements, design, testing, and project management.", "credits": 1, "department": "CS", "prerequisites": ["CS102"], "professor": "Chad Byers"},
    {"course_code": "CS404", "title": "Computer Networks", "description": "Protocols, routing, transport layer, and network security.", "credits": 1, "department": "CS", "prerequisites": ["CS201"], "professor": "Brian Howard"},
    {"course_code": "CS405", "title": "Operating Systems", "description": "Processes, memory management, file systems, and concurrency.", "credits": 1, "department": "CS", "prerequisites": ["CS201"], "professor": "Scott Thede"},
    {"course_code": "EE101", "title": "Introduction to Electrical Engineering", "description": "Circuit analysis, basic components, and DC/AC fundamentals.", "credits": 1, "department": "EE", "prerequisites": ["MATH101"], "professor": "Amy Sojot"},
    {"course_code": "EE102", "title": "Digital Logic Design", "description": "Boolean algebra, combinational and sequential logic, and basic digital systems.", "credits": 1, "department": "EE", "prerequisites": ["MATH101"], "professor": "Gary Lemon"},
    {"course_code": "EE201", "title": "Signals and Systems", "description": "Continuous and discrete-time signals, Fourier analysis, and linear systems.", "credits": 1, "department": "EE", "prerequisites": ["EE101", "MATH102"], "professor": "Kassahun Geleta"},
    {"course_code": "EE202", "title": "Electronics I", "description": "Semiconductor devices, diodes, transistors, and amplifiers.", "credits": 1, "department": "EE", "prerequisites": ["EE101"], "professor": "Gary Lemon"},
    {"course_code": "EE301", "title": "Control Systems", "description": "Feedback control, stability, and system design.", "credits": 1, "department": "EE", "prerequisites": ["EE201", "MATH201"], "professor": "Khadija Stewart"},
    {"course_code": "EE302", "title": "Communication Systems", "description": "Modulation, noise, and information theory basics.", "credits": 1, "department": "EE", "prerequisites": ["EE201", "MATH301"], "professor": "Kassahun Geleta"},
    {"course_code": "PHYS101", "title": "Physics I: Mechanics", "description": "Kinematics, dynamics, energy, and momentum.", "credits": 1, "department": "PHYS", "prerequisites": ["MATH101"], "professor": "Nipun Chopra"},
    {"course_code": "PHYS102", "title": "Physics II: Electricity and Magnetism", "description": "Electric fields, circuits, magnetic fields, and Maxwell's equations.", "credits": 1, "department": "PHYS", "prerequisites": ["PHYS101", "MATH102"], "professor": "Nipun Chopra"},
    {"course_code": "PHYS201", "title": "Waves and Optics", "description": "Wave motion, interference, diffraction, and geometric optics.", "credits": 1, "department": "PHYS", "prerequisites": ["PHYS102"], "professor": "Yanchao Yan"},
    {"course_code": "CHEM101", "title": "General Chemistry I", "description": "Atomic structure, bonding, stoichiometry, and thermochemistry.", "credits": 1, "department": "CHEM", "prerequisites": [], "professor": "Fatima Hussain"},
    {"course_code": "CHEM102", "title": "General Chemistry II", "description": "Equilibrium, kinetics, electrochemistry, and organic introduction.", "credits": 1, "department": "CHEM", "prerequisites": ["CHEM101"], "professor": "Fatima Hussain"},
    {"course_code": "BIO101", "title": "Introduction to Biology", "description": "Cell structure, genetics, evolution, and ecology.", "credits": 1, "department": "BIO", "prerequisites": [], "professor": "Allana Johnson"},
    {"course_code": "BIO102", "title": "Organismal Biology", "description": "Diversity of life, anatomy, and physiology.", "credits": 1, "department": "BIO", "prerequisites": ["BIO101"], "professor": "Ronald Dye"},
    {"course_code": "ECON101", "title": "Principles of Microeconomics", "description": "Supply and demand, market structure, and consumer behavior.", "credits": 1, "department": "ECON", "prerequisites": [], "professor": "Christine White"},
    {"course_code": "ECON102", "title": "Principles of Macroeconomics", "description": "National income, inflation, unemployment, and monetary policy.", "credits": 1, "department": "ECON", "prerequisites": [], "professor": "Christine White"},
    {"course_code": "ECON201", "title": "Intermediate Microeconomics", "description": "Utility maximization, production, and general equilibrium.", "credits": 1, "department": "ECON", "prerequisites": ["ECON101", "MATH101"], "professor": "David Alvarez"},
    {"course_code": "PSYCH101", "title": "Introduction to Psychology", "description": "Behavior, cognition, development, and research methods.", "credits": 1, "department": "PSYCH", "prerequisites": [], "professor": "Bin Qiu"},
    {"course_code": "PSYCH201", "title": "Statistics for Psychology", "description": "Descriptive and inferential statistics in behavioral research.", "credits": 1, "department": "PSYCH", "prerequisites": ["PSYCH101", "MATH101"], "professor": "Bin Qiu"},
    {"course_code": "ENGL101", "title": "Composition I", "description": "Academic writing, argumentation, and research.", "credits": 1, "department": "ENGL", "prerequisites": [], "professor": "Victoria Peters"},
    {"course_code": "ENGL102", "title": "Composition II", "description": "Advanced writing and literary analysis.", "credits": 1, "department": "ENGL", "prerequisites": ["ENGL101"], "professor": "Victoria Peters"},
    {"course_code": "HIST101", "title": "World History to 1500", "description": "Major civilizations and global developments.", "credits": 1, "department": "HIST", "prerequisites": [], "professor": "McKenzie Lamb"},
    {"course_code": "HIST102", "title": "World History since 1500", "description": "Modern world history and global interactions.", "credits": 1, "department": "HIST", "prerequisites": [], "professor": "McKenzie Lamb"},
    {"course_code": "PHIL101", "title": "Introduction to Philosophy", "description": "Ethics, epistemology, and major philosophical texts.", "credits": 1, "department": "PHIL", "prerequisites": [], "professor": "Bryon Black"},
    {"course_code": "PHIL201", "title": "Logic and Critical Thinking", "description": "Formal and informal logic, argument analysis.", "credits": 1, "department": "PHIL", "prerequisites": [], "professor": "Tierney McClure"},
    {"course_code": "STAT101", "title": "Introduction to Statistics", "description": "Data analysis, probability, and inference.", "credits": 1, "department": "STAT", "prerequisites": ["MATH101"], "professor": "Zhixin Wu"},
    {"course_code": "STAT201", "title": "Applied Regression", "description": "Linear and multiple regression, model selection.", "credits": 1, "department": "STAT", "prerequisites": ["STAT101", "MATH201"], "professor": "Zhixin Wu"},
    {"course_code": "ART101", "title": "Introduction to Visual Arts", "description": "Elements of design, color theory, and art history.", "credits": 1, "department": "ART", "prerequisites": [], "professor": "Victoria Peters"},
    {"course_code": "MUS101", "title": "Music Fundamentals", "description": "Notation, rhythm, harmony, and listening.", "credits": 1, "department": "MUS", "prerequisites": [], "professor": "Matthew Balensuela"},
    {"course_code": "CS406", "title": "Theory of Computation", "description": "Advanced topics in computability and complexity.", "credits": 1, "department": "CS", "prerequisites": ["CS202"], "professor": "Joey Mason"},
    {"course_code": "CS407", "title": "Distributed Systems", "description": "Consistency, replication, and fault tolerance.", "credits": 1, "department": "CS", "prerequisites": ["CS201", "CS404"], "professor": "Jeremy Anderson"},
    {"course_code": "CS408", "title": "Human-Computer Interaction", "description": "Usability, user research, and interface design.", "credits": 1, "department": "CS", "prerequisites": ["CS102"], "professor": "Joey Mason"},
    {"course_code": "CS409", "title": "Natural Language Processing", "description": "Text processing, parsing, and language models.", "credits": 1, "department": "CS", "prerequisites": ["CS301", "MATH201"], "professor": "Chad Byers"},
    {"course_code": "CS410", "title": "Computer Security", "description": "Cryptography, authentication, and secure design.", "credits": 1, "department": "CS", "prerequisites": ["CS201", "CS302"], "professor": "Khadija Stewart"},
    {"course_code": "MATH302", "title": "Numerical Methods", "description": "Numerical linear algebra, integration, and ODEs.", "credits": 1, "department": "MATH", "prerequisites": ["MATH102", "MATH201"], "professor": "Sutthirut Charoenphon"},
    {"course_code": "MATH401", "title": "Real Analysis", "description": "Rigorous treatment of limits, continuity, and integration.", "credits": 1, "department": "MATH", "prerequisites": ["MATH102", "MATH202"], "professor": "Zhixin Wu"},
    {"course_code": "EE303", "title": "Embedded Systems", "description": "Microcontrollers, real-time systems, and interfacing.", "credits": 1, "department": "EE", "prerequisites": ["EE102", "CS101"], "professor": "Justin Glessner"},
    {"course_code": "EE304", "title": "Power Systems", "description": "Generation, transmission, and distribution of electric power.", "credits": 1, "department": "EE", "prerequisites": ["EE101", "EE201"], "professor": "Jason Fuller"},
]


def main() -> None:
    db.init_db()
    created = 0
    updated = 0
    for c in COURSES:
        name = c.get("professor")
        professor_id = db.get_or_create_professor(name) if name else None
        existing = db.get_course_by_code(c["course_code"])
        if existing:
            db.set_course_professor(existing["id"], professor_id)
            updated += 1
            extra = f" — {name}" if name else ""
            print(f"Updated professor: {c['course_code']} - {c['title']}{extra}")
            continue
        try:
            db.insert_course(
                course_code=c["course_code"],
                title=c["title"],
                description=c["description"],
                credits=float(c["credits"]),
                department=c["department"],
                prerequisites=c["prerequisites"],
                professor_id=professor_id,
            )
            created += 1
            extra = f" — {name}" if name else ""
            print(f"Added: {c['course_code']} - {c['title']}{extra}")
        except db.CourseAlreadyExistsError:
            row = db.get_course_by_code(c["course_code"])
            if row:
                db.set_course_professor(row["id"], professor_id)
                updated += 1
                print(f"Updated professor: {c['course_code']}")
    print(
        f"\nDone. Created: {created}, Updated instructors: {updated}. "
        f"Total courses in seed list: {len(COURSES)}."
    )
 

if __name__ == "__main__":
    main()
