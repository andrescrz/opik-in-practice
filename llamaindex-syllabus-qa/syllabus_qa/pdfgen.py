"""Writes the fictional syllabus PDFs for Larkspur State University."""

import pathlib

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate

_styles = getSampleStyleSheet()
TITLE = ParagraphStyle("T", parent=_styles["Title"], fontName="Helvetica-Bold", fontSize=17)
HEAD = ParagraphStyle("H", parent=_styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, spaceBefore=12)
BODY = ParagraphStyle("B", parent=_styles["Normal"], fontName="Helvetica", fontSize=10.5, leading=14, spaceAfter=5)

SYLLABI = {
    "cs210-data-structures.pdf": (
        "CS 210: Data Structures and Algorithms",
        "Larkspur State University, Department of Computer Science, Fall term. Instructor: Dr. Imani Okoro.",
        [
            ("Prerequisites", [
                "Students must have completed CS 110 (Programming Fundamentals) with a grade of C or "
                "better and MATH 120 (Discrete Mathematics). Students who took CS 110 at another "
                "institution need the department's transfer approval before enrolling.",
            ]),
            ("Grading Policy", [
                "Final grades are weighted as follows: weekly programming labs 30%, two midterm exams "
                "at 15% each, a final project 20%, and the cumulative final exam 20%. The lowest lab "
                "score is dropped. A final average of 90% or above earns an A and 80% to 89.99% a B. "
                "You must earn at least 50% on the final exam to pass the course, whatever your "
                "overall average.",
            ]),
            ("Late Work", [
                "Labs submitted within 24 hours of the deadline lose 10% of the available points. "
                "After 24 hours, labs are not accepted unless you hold an approved extension. Each "
                "student gets two 48-hour extension tokens per term; request one in the course "
                "portal before the deadline. The final project cannot be extended.",
            ]),
            ("Office Hours", [
                "Dr. Okoro holds office hours Tuesdays and Thursdays from 2:00 to 4:00 PM in Hollis "
                "Hall room 318. Teaching assistants run a drop-in help room Mondays and Wednesdays "
                "from 5:00 to 7:00 PM in the Hollis Hall basement lab.",
            ]),
            ("Academic Integrity", [
                "You may discuss labs with classmates but must write your own code. Pasting code "
                "from an AI assistant without citing it counts as a violation and is reported to "
                "the Dean of Students.",
            ]),
        ],
    ),
    "bio150-intro-ecology.pdf": (
        "BIO 150: Introduction to Ecology",
        "Larkspur State University, Department of Biology, Fall term. Instructor: Dr. Tomas Verhaegen.",
        [
            ("Prerequisites", [
                "There are no formal prerequisites for BIO 150. Students who have completed BIO 100 "
                "or high-school AP Biology will find the first three weeks a review. The course "
                "satisfies the university's natural-science requirement.",
            ]),
            ("Grading Policy", [
                "Grades are weighted: field notebook 25%, four quizzes at 10% each (the lowest quiz "
                "is replaced by the average of the other three), a group field report 15%, and the "
                "final exam 20%. Attendance at the three Saturday field trips is mandatory; missing "
                "a field trip without a medical note lowers the final grade by one third of a "
                "letter grade, for example from B to B-minus.",
            ]),
            ("Late Work", [
                "The field notebook is collected every Friday at noon. A notebook handed in by the "
                "following Monday at noon loses 20% of that week's points. After Monday it earns "
                "zero for that week. Quizzes cannot be made up; use the quiz replacement rule "
                "instead. The group field report is penalized 5% per calendar day, up to five days.",
            ]),
            ("Office Hours", [
                "Dr. Verhaegen's office hours are Wednesdays from 10:00 AM to 12:00 noon in Marsh "
                "Science Building room 204, and by appointment on Fridays. Email "
                "ecology-help@larkspur.example at least a day ahead to book a Friday slot.",
            ]),
            ("Field Trip Logistics", [
                "Buses leave from the Marsh Science Building loading dock at 7:30 AM sharp. Bring "
                "waterproof boots and a charged phone for photo documentation.",
            ]),
        ],
    ),
    "hist301-atlantic-world.pdf": (
        "HIST 301: The Atlantic World, 1500-1800",
        "Larkspur State University, Department of History, Fall term. Instructor: Dr. Priya Nandakumar.",
        [
            ("Prerequisites", [
                "Students need one 100-level or 200-level history course, or instructor permission. "
                "HIST 301 is writing-intensive; students are expected to have completed ENG 101 "
                "(College Writing). Graduate students may enroll through HIST 501 with a longer "
                "final paper.",
            ]),
            ("Grading Policy", [
                "Grades are weighted: seminar participation 20%, three reading responses at 10% each, "
                "a primary-source analysis paper 20%, and a 4,000-word research paper 30%. There is "
                "no final exam. Participation is graded on contributions, not attendance alone, but "
                "more than three unexcused absences caps the participation grade at 50%.",
            ]),
            ("Late Work", [
                "Reading responses are due Sunday at 11:59 PM and are not accepted late; they are "
                "graded on a drop-nothing basis, so a missed response scores zero. Papers lose one "
                "third of a letter grade for each 24-hour period past the deadline, and a paper "
                "more than seven days late receives no credit. Documented illness or emergencies "
                "get an extension if you contact Dr. Nandakumar before the deadline.",
            ]),
            ("Office Hours", [
                "Dr. Nandakumar meets students Mondays from 1:00 to 3:00 PM in Aldridge Hall room "
                "12, and holds a virtual drop-in hour on Thursdays at 8:00 PM on the course video "
                "link. Paper conferences are booked through the department scheduler.",
            ]),
            ("Reading Materials", [
                "All readings are posted in the course portal as PDFs. The one required book, "
                "Cities of Salt and Sugar, is available at the campus bookstore.",
            ]),
        ],
    ),
}


def generate_all(out_dir: pathlib.Path) -> list[pathlib.Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for filename, (title, subtitle, sections) in SYLLABI.items():
        path = out_dir / filename
        doc = SimpleDocTemplate(
            str(path), pagesize=LETTER, leftMargin=inch, rightMargin=inch,
            topMargin=inch, bottomMargin=inch, title=title, author="Larkspur State University",
        )
        story = [Paragraph(title, TITLE), Paragraph(subtitle, BODY)]
        for heading, paragraphs in sections:
            story.append(Paragraph(heading, HEAD))
            story.extend(Paragraph(text, BODY) for text in paragraphs)
        doc.build(story)
        paths.append(path)
    return paths
