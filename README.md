# Fix RSpec Fails



*Troubleshoot tests is an essential software skill*


## Why Test Software:
Unit Tests are the front line defense against bugs and errors. Ultimately, end-users become your test subjects. Without automated tests, production deployments are more like crossing your fingers and hoping for the best.

Yet, even when the requirements are crystal clear, engineers make mistakes translating their understanding of requirements into executable code;

Unit tests force us to think and verify that our code exhibits certain behaviors. In this way, tests serve the same purpose as an editor and can guard typos that might result in syntax or type errors.

For interpreted languages like Ruby, this is especially helpful because many of the exceptions are run-time errors rather than compile-time errors.

Much like Rails, RSpec, in combination with libraries like factory_bot, Capybara, Timecop, etc. provides functionality that can easily seem like ruby magic.

## How RSpec Tests Fail:

Consistently failing tests are easier to catch and commonly the result of mental fatigue. Reproducibility in tests is important because, without it, developers question the value of tests and eventually testing itself.
 
RSpec does not explicitly require the use of test spies to make message expectations. Instead, it offers the receive matcher, which can be used on any object to make expectations about branching behavior. While this approach offers more convenient syntax, it can be easy to forget that the receiver matcher stubs target by default.

Let us consider an example:
Real estate 101 tells us that home prices only ever go up.



class House




 attr_accessor :price






 def appreciate_a_lot


   @price *= 1.08 # 8%


 end






 def appreciate_a_bit


   @price *= 1.02 # 2%


 end






 def appreciate


   if good_market?


     appreciate_a_lot


   else


     appreciate_a_bit


   end


 end


end


Now, we might want to test that assumption in RSpec:



describe House do




 it "always increases in value" do


   house = create(:house, price: 649000)


   allow(house).to receive(:good_market?).and_return(true)


   expect(house).to receive(:appreciate_a_lot)


   house.appreciate


   expect(house.price).to be > 649000


 end


end

Failure/Error: expect(house.price).to be > 649000

One strategy is to separate branch testing from results tests. This keeps test cases concise and avoids issues with inadvertently stubbing methods. A more general approach is to a stub as little as necessary to avoid discrepancies between test and production code paths. Most importantly, unlike the example above.
TL/DR: Remember, stubbing is the default behavior of the receivematcher; use and_call_original to un-stub but retain message expectations.

### State Preservation Across Tests:
Arne Hartherz’s article summarizes this well: Using before(:all) in RSpec will cause you lots of trouble unless you know what you are doing.
before(:all) creates data outside of transaction blocks, persisting changes across tests.
Best practice (which Rspec supports using the --order rand option) is to run tests in random order to reveal implicit dependencies between tests. Data that persists between randomly ordered tests naturally results in inconsistencies.

Here is one example of how not to use before(:all):


describe VotingBooth do




 before(:all) do


   @voter = VoterQueue.next


 end






 it "allows a voter to cast a ballot without error" do


   expect{ @voter.vote }.not_to raise_error


 end






 it "allows a voter to vote only once" do


   @voter.vote


   expect{ @voter.vote }.to raise_error(AlreadyVotedError)


 end


end


If the tests are run in the order they are defined, the second test will fail:
Failure/Error: raise AlreadyVotedError
This is why RSpec offers lazy-evaluated let, and eager-evaluated let!helper methods. When to use RSpec let offers more details, but in short:
Always prefer let to an instance variable.

### Side Effects

Active record callbacks
Active record offers convenient life cycle callbacks before and after state alteration that are easy to “set and forget”. Thorough testing should include these callbacks, but sometimes it is necessary to sidestep them.
That is where skip_callback comes in. It can be used both in a spec factory as well as individual tests. Consider a User model:
 
 
class User < ActiveRecord::Base 
 
 
 set_callback :create, :after, :send_welcome_email
 
  
 
 def send_welcome_email
 
   SendWelcomeEmail.perform_later(email)
 
 end
 
end

 
## Active Job QueueAdapters
A common use case for active record callbacks is to enqueue an active job. Under the hood, active job is configured to use a specific QueueAdapter. This adapter determines the queue order (like FIFO, LIFO, etc).
A common adapter for RSpec is the TestAdapter, which can be used to verifying that a specific job was enqueued successfully.
However, TestAdapter does not actually perform the job by default!
Depending on what you are testing, there are other adapters like the InlineAdapter that execute jobs immediately by treating perform_later calls like perform_now.
Alternatively, TestAdapter has a method, perform_enqueued_jobs, that, as its name suggests, actually performs the enqueued jobs synchronously.
 
 
describe User do
 
 
 let(:user) { create(:user) }
 
 
 
 describe "#send_welcome_email" do
 
   it "enqueues a SendWelcomeEmail job" do
 
     expect {
 
       user.send_welcome_email
 
     }.to have_enqueued(SendWelcomeEmail).exactly(1).times
 
   end
 
  
 
   it "sends the user a welcome email" do
 
     expect {
 
       perform_enqueued_jobs {
 
         user.send_welcome_email
 
       }
 
     }.to change{ ActionMailer::Base.deliveries.count }.by(1)
 
   end
 
 end
 
end

As with callbacks, there is value to testing both with and without actually performing the job. RSpec provides helpful active job matchers like the have_enqueued_job matcher.
These helper methods allow for separation of concerns, making it possible to test the logic of a job in one spec, and the logic that triggers the job in another.
Too Specific

Collections like Hashes and Arrays are used to store related data and are both enumerate in order of insertion.
During testing, this leads to comparisons that implicitly order specific, often when creating and comparing collections of active record models. For instance, a Cat can have many toys.



class Cat < ActiveRecord::Base




 has_many :toys


end

A simple test is then written to confirm that a Cat can in fact have many toys.



describe Cat do




 let(:lovie) { create(:cat, name: 'Lovie') }






 it "can haz multiple toys" do


   toys = create_list(:toy, 3, cat: lovie)


   expect(lovie.toys).to eq(toy)


 end


end


factory_bot’s create_list helper creates three toys associated with our cat, Lovie.

The issue here is that while create_list will return three unique toys ordered consistently by creation, the association will return based on the scope ordering. If no order is provided, it defaults to order by ID.
For sequential IDs, this should not pose an issue because ordering by creation or sequence should be identical. However, the first four digits of an ObjectID represents seconds since the Unix epoch.
Instead of using eq to compare two arrays, we can use the redundantly-named match_array matcher, which is independent of order.
### Warning:
Using expect { }.not_to raise_error(SpecificErrorClass) risks false positives, as literally any other error would cause the expectation to pass, including those raised by Ruby (e.g. NoMethodError, NameError, and ArgumentError), meaning the code you are intending to test may not even get reached.
Instead, consider using expect { }.not_to raise_error` or `expect { }.to raise_error(DifferentSpecificErrorClass).
The RSpec warning clearly explains the issue with this test.
In the example above, the second test actually raises TypeError: nil can’t be coerced into Fixnum as nowhere have we defined @sq_ft! That is the problem with overly-specific negative tests, they can miss real problems like this one.
#### Resources
Better Specs.
RSpec Style Guide.
Tests that sometimes fail.
It’s about time (zones).
How should I test randomness?
Flakey tests — The war that never ends.
RSpec: Thank you for running my tests in random order
How to set up Rails with RSpec, Capybara, and Database_cleaner.
 
