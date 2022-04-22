------------------
-- SAMPLE USERS --
------------------

-- Sample of users whose first post was in 2020-2021 --
  SELECT OwnerUserId as UserId
       , CreationDate as FirstPostDate
       , DATEADD(week, 4,  CreationDate) as InitiationPeriodEnd
       , DATEADD(week, 26, CreationDate) as ResponsePeriodEnd
       , DATEADD(week, 52, CreationDate) as RetentionPeriodEnd
    INTO #Sample
    FROM ( 
          SELECT *
               , ROW_NUMBER() OVER (PARTITION BY OwnerUserId ORDER BY CreationDate) as K
            FROM Posts
           WHERE PostTypeId = 1 -- question 
              OR PostTypeId = 2 -- answer
         ) as FirstPosts
   WHERE K = 1
     AND CreationDate BETWEEN '1-1-2020' AND '1-1-2021'
ORDER BY NEWID()
         OFFSET ##PageNo:int##*##RowsPerQuery:int## ROWS
   FETCH NEXT ##RowsPerQuery:int## ROWS ONLY;

CREATE TABLE #InitialPostData (
    UserId int
  , PostId int
  , PostType nvarchar(50)
  , Body nvarchar(max)
  , ViewCount int
  , Votes nvarchar(max)
  , Edits nvarchar(max)
  , Answers nvarchar(max)
  , Tags nvarchar(max)
);


-- Select all posts within initiation period (up to 4 weeks after
-- first post)
INSERT INTO #InitialPostData (UserId, PostId, PostType, Body, ViewCount)
SELECT s.UserId
     , p.Id
     , pt.Name
     , p.Body
     , p.ViewCount
  FROM #Sample as s
     , Posts as p
     , PostTypes as pt
 WHERE (p.PostTypeId = 1 OR p.PostTypeId = 2)
   AND p.OwnerUserId = s.UserId
   AND p.CreationDate < s.InitiationPeriodEnd
   AND pt.Id = p.PostTypeId;

-- Aggregate votes on initial posts made within the response period 
-- (up to 26 weeks after first post) 
  SELECT i.PostId
       , vt.Name
       , COUNT(*) as Count
    INTO #VoteData
    FROM #Sample as s
       , #InitialPostData as i
       , Votes as v
       , VoteTypes as vt
   WHERE v.PostId = i.PostId
     AND s.UserId = i.UserId
     AND v.CreationDate < s.ResponsePeriodEnd
     AND vt.Id = v.VoteTypeId
GROUP BY i.PostId, vt.Name;

UPDATE #InitialPostData 
   SET Votes = ( 
                 SELECT v.Name as VoteType
                      , v.Count
                   FROM #VoteData as v 
                  WHERE v.PostId = i.PostId 
                    FOR JSON PATH 
               )
  FROM #InitialPostData as i;

DROP TABLE #VoteData;

-- Aggregate suggested edits on initial posts made during response
-- period
  SELECT i.PostId
       , u.Id as EditorId
       , u.Reputation as EditorRep
       , DATEDIFF(day, u.CreationDate, se.CreationDate) as EditorAge
    INTO #EditData
    FROM #Sample as s
       , #InitialPostData as i
       , SuggestedEdits as se
       , Users as u
   WHERE se.PostId = i.PostId
     AND s.UserId = i.UserId
     AND se.CreationDate < s.ResponsePeriodEnd
     AND u.Id = se.OwnerUserId
GROUP BY i.PostId, u.Id, u.Reputation, u.CreationDate, se.CreationDate;

    UPDATE #InitialPostData 
       SET Edits = ( 
                     SELECT e.EditorId
                          , e.EditorRep
                          , e.EditorAge
                       FROM #EditData as e 
                      WHERE e.PostId = i.PostId 
                        FOR JSON PATH 
                   )
      FROM #InitialPostData as i
      
DROP TABLE #EditData;

-- Aggregate answers on initial posts during response period
SELECT i.PostId
     , u.Id as AnswererId
     , u.Reputation as AnswererRep
     , DATEDIFF(day, u.CreationDate, p.CreationDate) as AnswererAge
     , p.Body
  INTO #AnswerData
  FROM #Sample as s
     , #InitialPostData as i
     , Posts as p
     , Posts as q
     , Users as u
 WHERE p.ParentId = i.PostId
   AND q.Id = i.PostId
   AND p.PostTypeId = 2 -- answer
   AND s.UserId = i.UserId
   AND p.CreationDate < s.ResponsePeriodEnd
   AND u.Id = p.OwnerUserId;

UPDATE #InitialPostData 
   SET Answers = ( 
                   SELECT a.AnswererId
                        , a.AnswererRep
                        , a.AnswererAge
                        , a.Body
                     FROM #AnswerData as a 
                    WHERE a.PostId = i.PostId
                      FOR JSON PATH 
                 )
  FROM #InitialPostData as i;
  
DROP TABLE #AnswerData;

-- Aggregate tags
  SELECT i.PostId
       , t.TagName
       , COUNT(*) as Count
    INTO #TagData
    FROM #InitialPostData as i
       , Posts as p
       , PostTags as pt
       , Tags as t
   WHERE i.PostId = p.Id
     AND pt.PostId = COALESCE(p.ParentId, p.Id)
     AND t.Id = pt.TagId
GROUP BY i.PostId, t.TagName;

UPDATE #InitialPostData 
   SET Tags = ( 
                 SELECT t.TagName
                      , t.Count
                   FROM #TagData as t
                  WHERE t.PostId = i.PostId
                    FOR JSON PATH 
              )
  FROM #InitialPostData as i;

DROP TABLE #TagData;

-- Compile final dataset
CREATE TABLE #Dataset (
    UserId int
  , AccountCreationDate datetime
  , FirstPostDate datetime
  , NumFuturePosts int
  , PostsX varbinary(max)
);

INSERT INTO #Dataset (UserId, AccountCreationDate, FirstPostDate)
SELECT s.UserId 
     , u.CreationDate
     , s.FirstPostDate
  FROM #Sample as s
     , Users as u
 WHERE s.UserId = u.Id;
   
-- Data on future posts
WITH FuturePostData as (
    SELECT p.OwnerUserId as UserId
         , COUNT(*) as NumFuturePosts
      FROM Posts as p
         , #Sample as s
     WHERE p.OwnerUserId = s.UserId
       AND (p.PostTypeId = 1 OR p.PostTypeId = 2)
       AND p.CreationDate BETWEEN s.ResponsePeriodEnd AND s.RetentionPeriodEnd
  GROUP BY p.OwnerUserId
)    
    UPDATE #Dataset 
       SET NumFuturePosts = COALESCE(f.NumFuturePosts, 0)
      FROM #Dataset as d
 LEFT JOIN FuturePostData as f ON f.UserId = d.UserId;

-- Select and compress data on posts
    UPDATE #Dataset 
       SET PostsX = COMPRESS((
                      SELECT p.PostId
                           , p.PostType
                           , p.Body
                           , p.ViewCount
                           , JSON_QUERY(p.Votes) as Votes
                           , JSON_QUERY(p.Edits) as Edits
                           , JSON_QUERY(p.Answers) as Answers
                           , JSON_QUERY(p.Tags) as Tags
                        FROM #InitialPostData as p
                       WHERE p.UserId = d.UserId
                         FOR JSON PATH
                   ))
      FROM #Dataset as d

SELECT * FROM #Dataset;