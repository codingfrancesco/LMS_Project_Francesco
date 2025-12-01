from course_table import create_courses_table, insert_course
from topic_table import create_topics_table, insert_topic
from msq_table import create_msqs_table, insert_msq
from assignments_table import create_assignments_table, insert_assignments

create_courses_table()
insert_course("Physics","This is about physical sciences",1)

create_topics_table()
insert_topic(1,"chapter1")

create_msqs_table()
insert_msq(1,"what is physics?","table","a trouses","subject","moon","subject")

create_assignments_table()
insert_assignments(1,"Here are assignments","Math","Science physics")
insert_assignments(2,"Assignements that need to be done","History","Chemistry")
insert_assignments(3,"Here are assignments","Math","Science physics")
insert_assignments(4,"Here are assignments","Math","Science physics")
insert_assignments(5,"Here are assignments","Math","Science physics")
# others as homework



