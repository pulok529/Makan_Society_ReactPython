/*
Backfill plot numbers from the legacy member text field.

Safe to run multiple times.
It only updates rows where plot_no is blank/null.
*/

UPDATE society.members
SET plot_no = CASE
    WHEN plot_no IS NOT NULL AND LTRIM(RTRIM(plot_no)) <> '' THEN plot_no
    WHEN member_id_text IS NULL OR LTRIM(RTRIM(member_id_text)) = '' THEN NULL
    WHEN member_id_text LIKE 'Reg-%' THEN SUBSTRING(member_id_text, 5, LEN(member_id_text))
    ELSE member_id_text
END
WHERE plot_no IS NULL OR LTRIM(RTRIM(plot_no)) = '';

SELECT
    COUNT(*) AS total_members,
    SUM(CASE WHEN plot_no IS NOT NULL AND LTRIM(RTRIM(plot_no)) <> '' THEN 1 ELSE 0 END) AS members_with_plot_no
FROM society.members;
