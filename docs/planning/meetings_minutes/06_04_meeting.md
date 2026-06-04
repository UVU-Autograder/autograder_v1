# Minute Meeting: Thursday, 06/04/2026, 11:30 AM

Attendence: 
- Prof. Eshita 
- Prof. Ratul 
- Dominic 
- Easton 
- Jaxon 
- Keomony (Recorder)
- Vebjoern (scrum master)

## Progress Updates from Next week
- A list of FERPA questions is already compiled and those questions are already sent via email to the FERPA specialist

   Status: awaiting response 

- Working on integrating Monaco Editor with Next.js to verify functionality in the student sandbox environment. 

   Status: In-progress

- New version of student sanbox wireframes on Figma is in-progress.

   Status: In-progress  

## Discussion 
- A new software that monitoring online exams. (Honorlock)
- Hardware constraints: 
   - System memory is the main bottleneck. The server has 32 GB DDR5 RAM, and the combined overhead of Ubuntu, Next.js, FastAPI, and supporting services uses about 5.5–6 GB before student code execution.
   - Each student code execution container uses around 250 MB of memory per session. The base container footprint is around 80 MB, but capacity planning assumes 250 MB to account for runtime overhead and safety headroom.
   - The target is 50 concurrent executions, but current capacity is ~18–20 due to RAM constraints. The system is kept below ~75% memory utilization to avoid performance degradation or crashes 
- Redis Queue is proposed to manage workload. Instead of allowing unlimited simultaneous executions, submissions will be queued and processed in batches to stay within memory limits.
   - Redis queue will manage execution load by limiting concurrent jobs and queuing excess submissions. The system supports ~23–24 concurrent executions as the theoretical maximum under RAM constraints. Remaining jobs will be queued and processed sequentially. This may increase total processing time under heavy load, but ensures system stability.
- Frontend performance is not impacted under load and remains responsive for users viewing results. Impact is mainly on backend execution during bulk grading submissions, where memory constraints and queueing introduce processing delays.
- Suggestion: 
   - Switching kernel to be Firecracker instead of KEDA could save some memory but could only save a couple of gigabytes at max. So, 
   - Increasing RAM is the most effective way to improve concurrency and throughput.
- Student code is executed in isolated Docker containers managed by a virtualization layer (hypervisor), with each container sandboxed individually for test cases and consuming approximately ~250 MB of memory per student execution. 

## Next Week Expectation 
- The whole team is hoping to receive a response from FERPA 
- **Frontend Team** will be working on: 
   - **Vebjoern**: IDE-mulitple windows 
   - **Keomony**: Frontend Styling 
   - **Vebjoern and Dominic**: Test connectivity—integrating backend and frontend 
- **Backend Team** will be working on: 
   - **Jaxon**: 
      - Build the student sandbox API contract and temporary backend endpoints so Easton can implement the real ones once everything is set up
      - Start building the assignment/course config.json contract (if the first task above is finished earlier)
   - **Eason** working with frontend: 
      - Deploy a localized hardware environment for frontend and backend testing of a stripped down version of AutoGrader_V1 (ubuntu 24.xx, kata containers running Judge0, redis, celery, etc) and coordinate with **Vebjoern** to wire up frontend (nextJS, react, etc) test cases to ensure end-to-end pipeline with a single bundle. 
         - Will solidify the local network for static IP and provide **Vebjoern** with SSH + VPN credentials for tunneling and access until we get something on prem.
      - Verify with **Vebjoern** test cases, json payloads, and backend integration works with alpha build of frontend.
      - Provide **Vebjoern** with JSON POST and GET requests.

## Reference 
- [Honorlock replaces Proctorio starting Fall 2026](https://www.uvu.edu/facsenate/docs/2025-26-minutes-agendas/04.21.26_agenda.pdf)

