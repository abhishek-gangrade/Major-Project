import os
import random
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal, Base, engine
from backend.app.core.security import get_password_hash
from backend.app.core.config import settings
from backend.app.models.user import User
from backend.app.models.question import Question
from backend.app.models.attempt import Attempt, PracticeSession
from backend.app.models.proficiency import TopicProficiency
from backend.app.models.research import ResearchStudy, ResearchParticipant, AssessmentResult
from backend.app.services.performance_service import performance_service
from backend.app.services.research_service import research_service

# Authentic placement questions curated across all 9 topics
QUESTIONS_DATA = [
    # ---------------- Arrays ----------------
    {
        "topic": "Arrays",
        "difficulty": "Easy",
        "title": "Two Sum Indices",
        "statement": "Given an array of integers nums and an integer target, which algorithmic approach finds the indices of the two numbers that add up to target in O(n) time complexity?",
        "options": [
            "Nested loops comparing each pair in O(n^2)",
            "Hash Map storing complement values and their indices in O(n)",
            "Binary search on the unsorted array in O(n log n)",
            "Sorting the array first and returning the original indices without extra memory"
        ],
        "correct_answer": "Hash Map storing complement values and their indices in O(n)",
        "explanation": "Using a hash table allows O(1) average lookup for target - nums[i]. Iterating through the array once yields O(n) overall time and O(n) auxiliary space.",
        "expected_duration_seconds": 60
    },
    {
        "topic": "Arrays",
        "difficulty": "Medium",
        "title": "Maximum Subarray (Kadane's Algorithm)",
        "statement": "In Kadane's algorithm for finding the maximum contiguous subarray sum, what is the recurrence relation for the maximum ending at index i?",
        "options": [
            "max_ending_here = max(nums[i], max_ending_here + nums[i])",
            "max_ending_here = max_ending_here + nums[i]",
            "max_ending_here = max(0, max_ending_here - nums[i])",
            "max_ending_here = min(nums[i], max_ending_here + nums[i])"
        ],
        "correct_answer": "max_ending_here = max(nums[i], max_ending_here + nums[i])",
        "explanation": "Kadane's algorithm decides at each element whether to add it to the existing running sum or start a fresh subarray at nums[i].",
        "expected_duration_seconds": 90
    },
    {
        "topic": "Arrays",
        "difficulty": "Hard",
        "title": "Trapping Rain Water",
        "statement": "What is the optimal two-pointer space complexity to compute total trapped rain water between elevation bars represented as an array of non-negative integers?",
        "options": [
            "O(1) auxiliary space using left and right boundary pointers",
            "O(n) auxiliary space using prefix and suffix maximum arrays",
            "O(n^2) space using segment tree queries",
            "O(log n) space using divide and conquer recursion stack"
        ],
        "correct_answer": "O(1) auxiliary space using left and right boundary pointers",
        "explanation": "While prefix-suffix arrays take O(n) space, the two-pointer approach maintains left_max and right_max variables, reducing auxiliary space to O(1) in O(n) time.",
        "expected_duration_seconds": 120
    },

    # ---------------- Strings ----------------
    {
        "topic": "Strings",
        "difficulty": "Easy",
        "title": "Valid Anagram Check",
        "statement": "Which approach is most time-and-space efficient for checking if string s and string t are anagrams assuming ASCII lowercase characters?",
        "options": [
            "Count character frequencies in a fixed-size 26-element integer array in O(n) time and O(1) space",
            "Sort both strings and compare in O(n log n) time and O(n) space",
            "Generate all n! permutations of s and check if t is present in O(n!) time",
            "Compare each character of s against t using nested loops in O(n^2) time"
        ],
        "correct_answer": "Count character frequencies in a fixed-size 26-element integer array in O(n) time and O(1) space",
        "explanation": "A fixed frequency array of 26 integers allows single-pass counting in O(n) time with O(1) space complexity.",
        "expected_duration_seconds": 60
    },
    {
        "topic": "Strings",
        "difficulty": "Medium",
        "title": "Longest Substring Without Repeating Characters",
        "statement": "When using a sliding window with a hash map to find the longest substring without repeating characters, what action is taken when character s[right] is already in the map at index prev_idx >= left?",
        "options": [
            "Update left = prev_idx + 1 and update s[right]'s index in the map",
            "Reset left = 0 and clear the entire hash map",
            "Decrement right pointer by 1 and terminate",
            "Increment left by 1 and leave map unchanged"
        ],
        "correct_answer": "Update left = prev_idx + 1 and update s[right]'s index in the map",
        "explanation": "Advancing left directly to prev_idx + 1 skips all invalid duplicate prefixes in constant amortized steps.",
        "expected_duration_seconds": 90
    },
    {
        "topic": "Strings",
        "difficulty": "Hard",
        "title": "KMP Prefix Function (LPS Array)",
        "statement": "In the Knuth-Morris-Pratt (KMP) string matching algorithm, what does the Longest Proper Prefix which is also Suffix (LPS) array represent for pattern P[0..i]?",
        "options": [
            "The length of the longest proper prefix of P[0..i] that is also a suffix of P[0..i]",
            "The total number of unique substrings present in P[0..i]",
            "The lexicographical rank of the pattern suffix",
            "The count of repeated vowels in the pattern"
        ],
        "correct_answer": "The length of the longest proper prefix of P[0..i] that is also a suffix of P[0..i]",
        "explanation": "The LPS table stores the length of the longest proper prefix that matches a suffix, preventing redundant re-comparisons when a character mismatch occurs.",
        "expected_duration_seconds": 120
    },

    # ---------------- Searching and Sorting ----------------
    {
        "topic": "Searching and Sorting",
        "difficulty": "Easy",
        "title": "Binary Search Invariant",
        "statement": "What is the prerequisite for applying binary search on an array to find a target key in O(log n) time?",
        "options": [
            "The array must be sorted in monotonic order (ascending or descending)",
            "The array must only contain positive unique integers",
            "The array must be implemented as a linked list",
            "The array size must be a power of two"
        ],
        "correct_answer": "The array must be sorted in monotonic order (ascending or descending)",
        "explanation": "Binary search requires monotonic order so that comparing target with the middle element eliminates half of the remaining search space.",
        "expected_duration_seconds": 45
    },
    {
        "topic": "Searching and Sorting",
        "difficulty": "Medium",
        "title": "QuickSort Worst-Case Time Complexity",
        "statement": "Under which condition does standard QuickSort with first-element pivot selection exhibit its worst-case O(n^2) time complexity?",
        "options": [
            "When the input array is already sorted or reverse sorted",
            "When the array contains completely random permutations",
            "When all elements in the array are distinct and median is selected",
            "When the array size is smaller than 16 elements"
        ],
        "correct_answer": "When the input array is already sorted or reverse sorted",
        "explanation": "Selecting the first element as pivot on a sorted array results in completely unbalanced partitions of size 0 and n - 1 at each recursion level.",
        "expected_duration_seconds": 75
    },
    {
        "topic": "Searching and Sorting",
        "difficulty": "Hard",
        "title": "Search in Rotated Sorted Array",
        "statement": "In a rotated sorted array without duplicates (e.g., [4,5,6,7,0,1,2]), how do we determine which half of the array is normally ordered during binary search?",
        "options": [
            "If nums[left] <= nums[mid], the left half is monotonically sorted; otherwise the right half is sorted",
            "Check if nums[mid] is an even number",
            "Compare nums[mid] with target directly and assume left half is always sorted",
            "Sort the array first in O(n log n) before searching"
        ],
        "correct_answer": "If nums[left] <= nums[mid], the left half is monotonically sorted; otherwise the right half is sorted",
        "explanation": "In any rotated sorted array, at least one half of the partition between left and mid or mid and right must be monotonically sorted.",
        "expected_duration_seconds": 110
    },

    # ---------------- Basic Mathematics ----------------
    {
        "topic": "Basic Mathematics",
        "difficulty": "Easy",
        "title": "Greatest Common Divisor (Euclidean Algorithm)",
        "statement": "What is the recurrence step of the Euclidean algorithm for computing the greatest common divisor of two positive integers a and b (where a >= b)?",
        "options": [
            "gcd(a, b) = gcd(b, a % b), with base case gcd(a, 0) = a",
            "gcd(a, b) = gcd(a - 1, b - 1)",
            "gcd(a, b) = gcd(a * b, a / b)",
            "gcd(a, b) = a % b"
        ],
        "correct_answer": "gcd(a, b) = gcd(b, a % b), with base case gcd(a, 0) = a",
        "explanation": "Euclidean algorithm repeatedly reduces the pair (a, b) to (b, a % b) until the remainder becomes zero, running in O(log(min(a, b))) time.",
        "expected_duration_seconds": 50
    },
    {
        "topic": "Basic Mathematics",
        "difficulty": "Medium",
        "title": "Sieve of Eratosthenes Complexity",
        "statement": "What is the time complexity of the Sieve of Eratosthenes algorithm for finding all prime numbers up to n?",
        "options": [
            "O(n log(log n))",
            "O(n^2)",
            "O(n log n)",
            "O(sqrt(n))"
        ],
        "correct_answer": "O(n log(log n))",
        "explanation": "The sum of prime reciprocals up to n behaves asymptotically as log(log n), making the total operation count O(n sum_{p<=n} 1/p) = O(n log(log n)).",
        "expected_duration_seconds": 75
    },
    {
        "topic": "Basic Mathematics",
        "difficulty": "Hard",
        "title": "Modular Exponentiation",
        "statement": "What is the time complexity of calculating (base^exp) % mod using binary exponentiation (exponentiation by squaring)?",
        "options": [
            "O(log exp)",
            "O(exp)",
            "O(base * exp)",
            "O(mod)"
        ],
        "correct_answer": "O(log exp)",
        "explanation": "Binary exponentiation squares the base and halves the exponent at each bit of exp, achieving logarithmic O(log exp) time complexity.",
        "expected_duration_seconds": 90
    },

    # ---------------- Logical Reasoning ----------------
    {
        "topic": "Logical Reasoning",
        "difficulty": "Easy",
        "title": "Syllogism Deduction",
        "statement": "Statements: (1) All software engineers are problem solvers. (2) Some problem solvers are chess players. Conclusion: (I) All software engineers are chess players. (II) Some software engineers may be chess players. Which conclusion logically follows?",
        "options": [
            "Only II follows as a possibility",
            "Only I follows with certainty",
            "Both I and II follow with certainty",
            "Neither I nor II follows"
        ],
        "correct_answer": "Only II follows as a possibility",
        "explanation": "The intersection between engineers and chess players is not guaranteed universally, but an overlap is logically possible.",
        "expected_duration_seconds": 60
    },
    {
        "topic": "Logical Reasoning",
        "difficulty": "Medium",
        "title": "Circular Seating Arrangement",
        "statement": "Six persons (A, B, C, D, E, F) sit in a circle facing the center. A is opposite D. B is to the immediate right of A. E is between D and B. Who is sitting opposite B?",
        "options": [
            "F",
            "E",
            "C",
            "D"
        ],
        "correct_answer": "F",
        "explanation": "Placing A at pos 0 and D at pos 3: B is at pos 5 (right facing center). Since E is between D and B (pos 4), F and C occupy positions 1 and 2. F opposite B.",
        "expected_duration_seconds": 100
    },
    {
        "topic": "Logical Reasoning",
        "difficulty": "Hard",
        "title": "Truth-Tellers and Liars (Knights and Knaves)",
        "statement": "On an island, Knights always tell the truth and Knaves always lie. Person X says: 'Either I am a knave or person Y is a knight.' What can be concluded about X and Y?",
        "options": [
            "Both X and Y are Knights",
            "X is a Knave and Y is a Knight",
            "X is a Knight and Y is a Knave",
            "Both X and Y are Knaves"
        ],
        "correct_answer": "Both X and Y are Knights",
        "explanation": "If X were a Knave, his statement would be true (since he is a knave), contradiction. Thus X is a Knight (statement true). Since X is not a knave, Y must be a Knight.",
        "expected_duration_seconds": 120
    },

    # ---------------- SQL and DBMS ----------------
    {
        "topic": "SQL and DBMS",
        "difficulty": "Easy",
        "title": "ACID Properties Definition",
        "statement": "Which ACID property guarantees that once a transaction has been committed, its changes will survive system crashes or power failures?",
        "options": [
            "Durability",
            "Atomicity",
            "Consistency",
            "Isolation"
        ],
        "correct_answer": "Durability",
        "explanation": "Durability ensures committed transaction changes are written to non-volatile storage (such as Write-Ahead Logs) and persist across crashes.",
        "expected_duration_seconds": 45
    },
    {
        "topic": "SQL and DBMS",
        "difficulty": "Medium",
        "title": "Second Highest Salary Query",
        "statement": "Which standard SQL query reliably retrieves the 2nd highest distinct salary from the Employee table?",
        "options": [
            "SELECT MAX(salary) FROM Employee WHERE salary < (SELECT MAX(salary) FROM Employee);",
            "SELECT salary FROM Employee ORDER BY salary DESC LIMIT 1 OFFSET 2;",
            "SELECT salary FROM Employee WHERE salary = 2;",
            "SELECT DISTINCT salary FROM Employee GROUP BY salary HAVING COUNT(*) = 2;"
        ],
        "correct_answer": "SELECT MAX(salary) FROM Employee WHERE salary < (SELECT MAX(salary) FROM Employee);",
        "explanation": "Subquery `SELECT MAX(salary) FROM Employee WHERE salary < (SELECT MAX(salary)...)` cleanly handles ties and works across all SQL dialects.",
        "expected_duration_seconds": 75
    },
    {
        "topic": "SQL and DBMS",
        "difficulty": "Hard",
        "title": "B+ Tree vs B Tree in Database Indexing",
        "statement": "Why do relational database storage engines (such as InnoDB and PostgreSQL) prefer B+ Trees over standard B Trees for index structures?",
        "options": [
            "B+ Trees store all actual record pointers in leaf nodes linked sequentially, enabling rapid range scans and higher branching factor in internal nodes",
            "B+ Trees require zero memory for internal nodes",
            "B+ Trees prevent phantom reads without transaction locks",
            "B+ Trees are strictly binary trees that minimize pointer sizes"
        ],
        "correct_answer": "B+ Trees store all actual record pointers in leaf nodes linked sequentially, enabling rapid range scans and higher branching factor in internal nodes",
        "explanation": "Because internal nodes only hold search keys and not data records, fan-out is higher (fewer disk I/O levels), and doubly-linked leaves make range scans O(k) sequential reads.",
        "expected_duration_seconds": 110
    },

    # ---------------- Operating Systems ----------------
    {
        "topic": "Operating Systems",
        "difficulty": "Easy",
        "title": "Process vs Thread Memory Sharing",
        "statement": "What resource is shared directly between multiple threads belonging to the same operating system process?",
        "options": [
            "Code segment, data segment, and open file descriptors",
            "Call stack and thread-local CPU registers",
            "Process ID and individual memory virtual address space isolation",
            "Separate physical CPU cores exclusively"
        ],
        "correct_answer": "Code segment, data segment, and open file descriptors",
        "explanation": "Threads of the same process share the heap, data, code segment, and file descriptors, but each thread maintains its own stack and register context.",
        "expected_duration_seconds": 50
    },
    {
        "topic": "Operating Systems",
        "difficulty": "Medium",
        "title": "Deadlock Coffman Conditions",
        "statement": "Which of the following is NOT one of the four necessary Coffman conditions for a deadlock to occur?",
        "options": [
            "Preemptive resource allocation",
            "Mutual exclusion",
            "Hold and wait",
            "Circular wait"
        ],
        "correct_answer": "Preemptive resource allocation",
        "explanation": "The condition is 'No preemption' (resources cannot be forcibly taken away). Preemptive allocation prevents deadlocks from occurring.",
        "expected_duration_seconds": 70
    },
    {
        "topic": "Operating Systems",
        "difficulty": "Hard",
        "title": "Virtual Memory and Translation Lookaside Buffer (TLB)",
        "statement": "In a 2-level paging scheme where memory access time is 100ns and TLB access time is 20ns, what is the Effective Memory Access Time (EMAT) if the TLB hit ratio is 90%?",
        "options": [
            "140 ns",
            "120 ns",
            "220 ns",
            "100 ns"
        ],
        "correct_answer": "140 ns",
        "explanation": "Hit time = 20 + 100 = 120ns. Miss time = 20 + 100 (level 1) + 100 (level 2) + 100 (data) = 320ns. EMAT = 0.90*(120) + 0.10*(320) = 108 + 32 = 140 ns.",
        "expected_duration_seconds": 120
    },

    # ---------------- Computer Networks ----------------
    {
        "topic": "Computer Networks",
        "difficulty": "Easy",
        "title": "TCP vs UDP Reliability",
        "statement": "Which protocol mechanism enables Transmission Control Protocol (TCP) to provide reliable in-order byte stream delivery compared to UDP?",
        "options": [
            "Sequence numbers, cumulative acknowledgments, and retransmission timeouts",
            "Broadcasting packets to all subnet devices simultaneously",
            "Eliminating checksum validation for faster payload throughput",
            "Using static routing tables at host interfaces"
        ],
        "correct_answer": "Sequence numbers, cumulative acknowledgments, and retransmission timeouts",
        "explanation": "TCP tracks byte sequences via sequence numbers and ACK packets, triggering retransmission upon timeout or 3 duplicate ACKs.",
        "expected_duration_seconds": 50
    },
    {
        "topic": "Computer Networks",
        "difficulty": "Medium",
        "title": "Subnet Masking (CIDR)",
        "statement": "How many usable host IP addresses are available in a subnetwork with CIDR notation 192.168.10.0/26?",
        "options": [
            "62",
            "64",
            "126",
            "30"
        ],
        "correct_answer": "62",
        "explanation": "A /26 prefix leaves 32 - 26 = 6 host bits. 2^6 = 64 total addresses. Subtracting network address (all 0s) and broadcast address (all 1s) yields 62 usable hosts.",
        "expected_duration_seconds": 75
    },
    {
        "topic": "Computer Networks",
        "difficulty": "Hard",
        "title": "TCP Congestion Control (Fast Recovery)",
        "statement": "What triggers TCP Reno to enter Fast Retransmit and Fast Recovery rather than resetting cwnd to 1 MSS?",
        "options": [
            "Arrival of 3 duplicate ACKs for the same sequence number",
            "Retransmission timer expiration (RTO)",
            "Reception of an ICMP destination unreachable message",
            "TCP SYN segment timeout"
        ],
        "correct_answer": "Arrival of 3 duplicate ACKs for the same sequence number",
        "explanation": "Three duplicate ACKs indicate packet loss while packets behind it are still arriving, prompting TCP Reno to retransmit the missing segment and halve cwnd.",
        "expected_duration_seconds": 105
    },

    # ---------------- Dynamic Programming ----------------
    {
        "topic": "Dynamic Programming",
        "difficulty": "Easy",
        "title": "Climbing Stairs (Fibonacci Relation)",
        "statement": "You are climbing a staircase with n steps. Each time you can climb either 1 or 2 steps. What is the recurrence relation for the number of distinct ways dp[i] to reach step i?",
        "options": [
            "dp[i] = dp[i-1] + dp[i-2]",
            "dp[i] = dp[i-1] * dp[i-2]",
            "dp[i] = max(dp[i-1], dp[i-2])",
            "dp[i] = dp[i-1] + 1"
        ],
        "correct_answer": "dp[i] = dp[i-1] + dp[i-2]",
        "explanation": "To reach step i, one must come from step i-1 (taking 1 step) or step i-2 (taking 2 steps), identical to Fibonacci recurrence.",
        "expected_duration_seconds": 45
    },
    {
        "topic": "Dynamic Programming",
        "difficulty": "Medium",
        "title": "0/1 Knapsack Decision Recurrence",
        "statement": "In the 0/1 Knapsack problem with weights w[i] and values v[i], what is the recurrence relation for dp[i][w] when w >= w[i]?",
        "options": [
            "dp[i][w] = max(dp[i-1][w], v[i] + dp[i-1][w - w[i]])",
            "dp[i][w] = dp[i-1][w] + v[i]",
            "dp[i][w] = max(dp[i][w-1], v[i] + dp[i][w - w[i]])",
            "dp[i][w] = min(dp[i-1][w], v[i] + dp[i-1][w - w[i]])"
        ],
        "correct_answer": "dp[i][w] = max(dp[i-1][w], v[i] + dp[i-1][w - w[i]])",
        "explanation": "At item i, we either exclude item i (dp[i-1][w]) or include it (v[i] + dp[i-1][w - w[i]]), taking the maximum value.",
        "expected_duration_seconds": 90
    },
    {
        "topic": "Dynamic Programming",
        "difficulty": "Hard",
        "title": "Longest Increasing Subsequence (Patience Sorting)",
        "statement": "What is the optimal time complexity to find the length of the Longest Increasing Subsequence (LIS) of an array of n integers using binary search with patience sorting tails?",
        "options": [
            "O(n log n)",
            "O(n^2)",
            "O(n * sqrt(n))",
            "O(2^n)"
        ],
        "correct_answer": "O(n log n)",
        "explanation": "Maintaining a tails array where tails[i] stores the smallest tail of all increasing subsequences of length i+1 allows binary search placement in O(log n) for each of n items, achieving O(n log n) overall.",
        "expected_duration_seconds": 120
    }
]


def seed_database():
    """Initializes tables, creates admin & student accounts, seeds curated questions and demo performance."""
    print("Creating database schema...")
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # 1. Admin User
        admin_email = "admin@adaptiveprep.edu"
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(
                display_name="Prof. HarshPratap Singh (Admin)",
                email=admin_email,
                password_hash=get_password_hash("AdminPass123!"),
                role="admin",
                is_active=True,
            )
            db.add(admin)
            print(f"Created Administrator account: {admin_email}")

        # 2. Demo Student Account
        student_email = "student@adaptiveprep.edu"
        student = db.query(User).filter(User.email == student_email).first()
        if not student:
            student = User(
                display_name="Abhishek Gangrade",
                email=student_email,
                password_hash=get_password_hash("StudentPass123!"),
                role="student",
                is_active=True,
            )
            db.add(student)
            print(f"Created Student account: {student_email}")

        # 3. Second Student Account for Teamwork Demo
        student2_email = "aastha@adaptiveprep.edu"
        student2 = db.query(User).filter(User.email == student2_email).first()
        if not student2:
            student2 = User(
                display_name="Aastha Jain",
                email=student2_email,
                password_hash=get_password_hash("StudentPass123!"),
                role="student",
                is_active=True,
            )
            db.add(student2)
            print(f"Created Student account: {student2_email}")

        db.commit()
        db.refresh(student)

        # 4. Seed Questions across 9 topics
        existing_count = db.query(Question).count()
        if existing_count == 0:
            print(f"Seeding {len(QUESTIONS_DATA)} curated placement questions...")
            for q_data in QUESTIONS_DATA:
                q = Question(
                    title=q_data["title"],
                    statement=q_data["statement"],
                    topic=q_data["topic"],
                    difficulty=q_data["difficulty"],
                    question_type="mcq",
                    options=q_data["options"],
                    correct_answer=q_data["correct_answer"],
                    explanation=q_data["explanation"],
                    expected_duration_seconds=q_data["expected_duration_seconds"],
                    is_active=True,
                )
                db.add(q)
            db.commit()
            print("Question bank seeded successfully.")

        # 5. Seed Authentic Demo Attempts & Recalculate Proficiency for Abhishek
        student_attempts_count = db.query(Attempt).filter(Attempt.user_id == student.id).count()
        if student_attempts_count == 0:
            print("Generating initial demo attempts for student profile visualization...")
            questions = db.query(Question).all()
            
            # Select 12 questions across different topics and simulate realistic student practice
            random.seed(42)
            sample_qs = questions[:12]
            
            # Create a demo practice session
            session = PracticeSession(
                user_id=student.id,
                practice_mode="adaptive",
                started_at=datetime.now(timezone.utc) - timedelta(hours=2),
                ended_at=datetime.now(timezone.utc) - timedelta(minutes=10),
                is_completed=True,
            )
            db.add(session)
            db.commit()
            db.refresh(session)

            for idx, q in enumerate(sample_qs):
                # Simulate high proficiency in Arrays/DBMS, moderate in DP/Networks
                is_corr = True if idx % 4 != 0 else False
                ans = q.correct_answer if is_corr else q.options[(q.options.index(q.correct_answer) + 1) % len(q.options)]
                time_taken = q.expected_duration_seconds + random.randint(-15, 20)
                
                attempt = Attempt(
                    user_id=student.id,
                    question_id=q.id,
                    session_id=session.id,
                    submitted_answer=ans,
                    is_correct=is_corr,
                    time_taken_seconds=max(20, time_taken),
                    difficulty_at_attempt=q.difficulty,
                    algorithm_version=settings.ALGORITHM_VERSION,
                    attempt_timestamp=datetime.now(timezone.utc) - timedelta(minutes=(12 - idx) * 8),
                )
                db.add(attempt)
            db.commit()

            # Recalculate topic proficiencies for student
            topics = list(set(q.topic for q in sample_qs))
            for t in topics:
                performance_service.recalculate_topic_proficiency(db, student.id, t)
            print("Demo attempts and proficiency estimates established.")

        # 6. Seed Research Study & Participant Records
        study = research_service.get_or_create_default_study(db)
        participant_count = db.query(ResearchParticipant).filter(ResearchParticipant.study_id == study.id).count()
        if participant_count == 0:
            print("Seeding research evaluation dataset (Adaptive vs Accuracy-Only vs Random)...")
            strategies = ["adaptive", "accuracy_only", "random"]
            random.seed(101)

            # Generate 45 pseudonymous participants (15 per condition)
            for i in range(1, 46):
                strat = strategies[(i - 1) % 3]
                p_code = f"PART-{1000 + i}-{strat[:4].upper()}"
                
                participant = ResearchParticipant(
                    study_id=study.id,
                    participant_code=p_code,
                    assigned_strategy=strat,
                    enrollment_metadata={"cohort": "CSE-2026", "semester": 8},
                    consent_given=True,
                    status="completed",
                    enrolled_at=datetime.now(timezone.utc) - timedelta(days=14),
                )
                db.add(participant)
                db.commit()
                db.refresh(participant)

                # Simulate baseline pre-test and outcome post-test
                # Adaptive strategy demonstrates superior score gain in the simulated evaluation
                base_pre = random.randint(45, 65)
                if strat == "adaptive":
                    gain = random.randint(18, 28)
                elif strat == "accuracy_only":
                    gain = random.randint(10, 18)
                else:  # random
                    gain = random.randint(2, 10)
                
                post_score = min(100, base_pre + gain)

                pre_result = AssessmentResult(
                    study_id=study.id,
                    participant_id=participant.id,
                    assessment_type="pre_test",
                    score=float(base_pre),
                    max_score=100.0,
                    percentage=float(base_pre),
                    time_taken_seconds=random.randint(600, 900),
                    completed_at=datetime.now(timezone.utc) - timedelta(days=13),
                )
                post_result = AssessmentResult(
                    study_id=study.id,
                    participant_id=participant.id,
                    assessment_type="post_test",
                    score=float(post_score),
                    max_score=100.0,
                    percentage=float(post_score),
                    time_taken_seconds=random.randint(550, 800),
                    completed_at=datetime.now(timezone.utc) - timedelta(days=2),
                )
                db.add(pre_result)
                db.add(post_result)

            db.commit()
            print("Research study dataset seeded successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

