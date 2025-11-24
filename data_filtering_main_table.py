import pandas as pd
import sqlite3

data = [
    ('Forever Free LMS', 'https://www.talentlms.com', 'https://www.linkedin.com/company/invince', '51-200 employees', 'Pune, Maharashtra', 'Forever Free LMS'),
    ('PPT-to-SCORM authoring tool', 'https://www.ispringsolutions.com', 'https://www.linkedin.com/company/scormhero', '2-10 employees', 'Middletown, DE', 'PPT-to-SCORM authoring tool'),
    ('TIME for Kids', 'https://www.timeforkids.com', 'https://www.linkedin.com/company/time-for-kids-informationstechnologien-gmbh', '11-50 employees', 'Berlin', 'TIME for Kids'),
    ('TIME Edge', 'https://www.timeedge.com', 'https://www.linkedin.com/company/on-time-edge', '51-200 employees', 'Centennial, CO', 'TIME Edge'),
    ('TIME Cover Store', 'https://timecoverstore.com', 'https://www.linkedin.com/company/coverstore', '51-200 employees', 'Carrollton, Texas', 'TIME Cover Store'),
    ('Digital Magazine', 'https://geo.ema.gs', 'https://www.linkedin.com/company/digitalmagazine', '11-50 employees', 'New York, New York', 'Digital Magazine'),
    ('CYPHER Learning', 'https://www.cypherlearning.com', 'https://www.linkedin.com/company/cypher-learning', '51-200 employees', 'Plano, Texas', 'CYPHER Learning'),
    ('Advertise', 'http://www.forbesmedia.com', None, None, None, None),
    ('Dr. Lynch’s Personal Website', 'http://www.drmattlynch.com', 'https://www.linkedin.com/company/lynch-regenerative-medicine', '11-50 employees', 'Franklin, TN', 'Dr. Lynch’s Personal Website'),
    ('Books', 'https://www.theedadvocate.org', 'https://www.linkedin.com/company/books-and-books', '51-200 employees', 'Coral Gables, Florida', 'Books'),
    ('Post a Job', 'https://p-20edcareers.com', None, None, None, None),
    ('PEDAGOGUE', 'https://pedagogue.app', 'https://www.linkedin.com/company/pedagogue-ai-training', '2-10 employees', 'London, Greater London', 'PEDAGOGUE'),
    ('SCHOOL RATINGS', 'https://edrater.com', 'https://www.linkedin.com/company/greatschools', '11-50 employees', 'Oakland, California', 'SCHOOL RATINGS'),
    ('market is saturated', 'https://www.grandviewresearch.com', None, None, None, None),
    ('“Great Skills Disruption”', 'https://www.weforum.org', None, None, None, None),
    ('30-50% higher retention rates', 'https://www.deloitte.com', None, None, None, None),
    ('Guild', 'https://guild.com', 'https://www.linkedin.com/company/guildeducation', '1K-5K employees', 'Denver, CO', 'Guild'),
    ('Coursera for Business', 'https://www.coursera.org', 'https://www.linkedin.com/company/coursera', '1K-5K employees', 'Mountain View, CA', 'Coursera for Business'),
    ('Degreed', 'https://degreed.com', 'https://www.linkedin.com/company/degreed', '501-1K employees', 'Pleasanton, California', 'Degreed'),
    ('Articulate 360', 'https://www.articulate.com', 'https://www.linkedin.com/company/articulate', '201-500 employees', 'New York', 'Articulate 360'),
    ('Udemy Business', 'https://business.udemy.com', 'https://www.linkedin.com/company/udemy', '1K-5K employees', 'San Francisco, CA', 'Udemy Business'),
    ('Pluralsight', 'https://www.pluralsight.com', 'https://www.linkedin.com/company/pluralsight', '1K-5K employees', 'Westlake, Texas', 'Pluralsight'),
    ('SC Training', 'https://training.safetyculture.com', 'https://www.linkedin.com/company/sctrainingllc', '0-1 employees', 'Tampa, Florida', 'SC Training'),
    ('ODR Portal', 'https://smartodr.in', 'https://www.linkedin.com/company/cadreodr', '11-50 employees', 'Bengaluru, Karnataka', 'ODR Portal')
]

columns = ['company_name', 'website', 'linkedin_url', 'size', 'hq', 'original_search']
df = pd.DataFrame(data, columns=columns)

df_clean = df.dropna()

db_name = "companies_url.db"
table_name = "clean_main_table"

conn = sqlite3.connect(db_name)

df_clean.to_sql(table_name, conn, if_exists='replace', index=False)

conn.close()
