from models.request_reseponse_models import UserDetails
from openai import OpenAI
import os, asyncio, json
from config.my_logger import get_logger
logger = get_logger(__name__,"sherlock_ai")

from config.env_vars import load_config
load_config()

OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")
OPEN_ROUTER_API_BASE_URL = os.getenv("OPEN_ROUTER_API_BASE_URL")
OPEN_ROUTER_MODEL_NAME = os.getenv("OPEN_ROUTER_MODEL_NAME")

class SherlockAI:
    def __init__(self):
        self.client = OpenAI(
            base_url=OPEN_ROUTER_API_BASE_URL,
            api_key=OPEN_ROUTER_API_KEY
        )
        self.model_name = OPEN_ROUTER_MODEL_NAME
        self.thirty_day_workout_plan_prompt_template = self.load_thirty_day_workout_plan_prompt_template()
        self.json_response_schema_template = self.load_json_response_schema_template()
        self.firstpart_workout_prompt_template = self.load_firstpart_workout_prompt_template()
        self.secondpart_workout_prompt_template = self.load_secondpart_workout_prompt_template()
        self.thirdpart_workout_prompt_template = self.load_thirdpart_workout_prompt_template()
        self.sample_ai_json_response = self.load_sample_ai_json_response()

    def load_sample_ai_json_response(self) -> str:
        sample_res = os.path.join(os.path.dirname(__file__), 'response_format', 'sample-workout-program-res.json')
        try:
            with open(sample_res, 'r') as file:
                json_str = file.read()
                # json_data = json.loads(json_str)
            return json_str
        except FileNotFoundError:
            logger.error(f"LOADING JSON SCHEMA:: file not found. file path: {sample_res}")
            # handle the error as needed
            return {"status" : "error", "message": "JSON response schema file not found."}


    def load_thirty_day_workout_plan_prompt_template(self) -> str:
        # Placeholder for loading the actual prompt template
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'workout_plan_prompt.txt')
        try:
            with open(prompt_path, 'r') as file:
                prompt_template = file.read()
            return prompt_template
        except FileNotFoundError:
            logger.error("Prompt template file not found.")
            # handle the error as needed
            return {"status" : "error", "message": "Prompt template file not found."}
        
    def load_json_response_schema_template(self) -> str:
        prompt_path = os.path.join(os.path.dirname(__file__), 'response_format', 'workout_plan_schema.json')
        try:
            with open(prompt_path, 'r') as file:
                json_str = file.read()
                # json_data = json.loads(json_str)
            return json_str
        except FileNotFoundError:
            logger.error(f"LOADING JSON SCHEMA:: file not found. file path: {prompt_path}")
            # handle the error as needed
            return {"status" : "error", "message": "JSON response schema file not found."}
        
    def load_firstpart_workout_prompt_template(self) -> str:
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'firstpart_workout_prompt.txt')
        try:
            with open(prompt_path, 'r') as file:
                prompt_template = file.read()
            return prompt_template
        except FileNotFoundError:
            logger.error("LOADING FIRST PART WORKOUT:: file not found.")
            return {"status" : "error", "message": "First workout prompt template file not found."}

    def load_secondpart_workout_prompt_template(self) -> str:
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'secondpart_workout_prompt.txt')
        try:
            with open(prompt_path, 'r') as file:
                prompt_template = file.read()
            return prompt_template
        except FileNotFoundError:
            logger.error("LOADING SECOND PART WORKOUT:: file not found.")
            # handle the error as needed
            return {"status" : "error", "message": "Second workout prompt template file not found."}
        
    def load_thirdpart_workout_prompt_template(self) -> str:
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'thirdpart_workout_prompt.txt')
        try:
            with open(prompt_path, 'r') as file:
                prompt_template = file.read()
            return prompt_template
        except FileNotFoundError:
            logger.error("LOADING THIRD PART WORKOUT:: file not found.")
            # handle the error as needed
            return {"status" : "error", "message": "Third workout prompt template file not found."}
        
    
    def convert_userdetails_to_text(self, user_details: UserDetails) -> str:
        return f"""
            id: {user_details.id}
            Name: {user_details.name}
            Age: {user_details.age}
            Weight: {user_details.weight}
            Height: {user_details.height}
            Fitness Level: {user_details.fitness_level}
            Fitness Goal: {user_details.fitness_goal}
            Workout Location: {user_details.work_out_location}
            Days Available: {', '.join([d.value if hasattr(d, 'value') else str(d) for d in user_details.days_availability])}
            Equipment: {', '.join([e.value if hasattr(e, 'value') else str(e) for e in user_details.equipment_availability])}
            Notes: {user_details.notes if user_details.notes else "No notes provided"}
            Start Date: {user_details.date_now}
            """
            
    def convert_user_dict_to_text(self, user_dict: dict) -> str:
        return f"""
            id: {user_dict.get('id')}
            Name: {user_dict.get('name')}
            Age: {user_dict.get('age')}
            Gender: {user_dict.get('gender')}
            Weight: {user_dict.get('weight')}
            Height: {user_dict.get('height')}
            Fitness Level: {user_dict.get('fitnessLevel')}
            Fitness Goal: {user_dict.get('fitnessGoal')}
            Workout Location: {user_dict.get('workoutLocation')}
            Days Available: {', '.join([d.value if hasattr(d, 'value') else str(d) for d in user_dict.get('daysAvailability', [])])}
            Equipment: {', '.join([e.value if hasattr(e, 'value') else str(e) for e in user_dict.get('equipmentAvailability', [])])}
            Notes: {user_dict.get('notes')}
            Start Date: {user_dict.get('start_date')}
            """

    def get_minified_json(self, content: str) -> str:
        """Minify JSON (removes \n/whitespace)."""
        parsed = json.loads(content)
        return json.dumps(parsed, separators=(',', ':'), ensure_ascii=False)
    
    def merge_workout_parts(self, part1: dict, part2: dict, part3: dict) -> dict:
        """Merge 3 partials into full 30-day plan."""
        full = {
            "user_id": part1["user_id"],
            "start_date": part1["start_date"],
            "total_days": 30,
            "notes_from_coach": part1["notes_from_coach"],  # Only from part1
            "plan": part1["plan"] + part2["plan"] + part3["plan"]  # 30 days!
        }
        # Validate: 30 items?
        if len(full["plan"]) != 30:
            raise ValueError("Merge failed: plan not 30 days")
        return full
    
    # def generate_workout_plan_test(self, user_details: UserDetails) -> str:
    def generate_workout_plan(self, user_details: dict) -> str:
        """
        Orchestrates 3 parts → merges → returns full minified JSON.
        Call THIS instead of individual funcs.
        """
        try:
            # user_text = self.convert_userdetails_to_text(user_details)
            user_text = self.convert_user_dict_to_text(user_details)
            response_schema = self.json_response_schema_template

            logger.info("TEST WORKOUT PLAN GENERATION")
            logger.info(f"AIIII: P1:: {self.firstpart_workout_prompt_template.replace('INPUT_JSON_HERE', user_text).replace('INPUT_JSON_RESPONSE_SCHEMA', response_schema)}")
            logger.info(f"AIIII: P2:: {self.secondpart_workout_prompt_template.replace('INPUT_JSON_HERE', user_text).replace('INPUT_JSON_RESPONSE_SCHEMA', response_schema)}")
            logger.info(f"AIIII: P3:: {self.thirdpart_workout_prompt_template.replace('INPUT_JSON_HERE', user_text).replace('INPUT_JSON_RESPONSE_SCHEMA', response_schema)}")
            logger.info(f"MANDONG USER TEXT: {user_text}")
            logger.info(f"MANDONG USER DICTIONARY: {user_details}")
            # return "test"
            
            messages1 = [
                {"role": "system", "content": "You are a fitness expert..."},
                {"role": "user", "content": self.firstpart_workout_prompt_template.replace("INPUT_JSON_HERE", user_text).replace("INPUT_JSON_RESPONSE_SCHEMA", response_schema)}
            ]
            
            # Part 1: Days 1-10
            part1_raw = self._call_api(user_text, messages1, is_first=True)
            part1 = json.loads(part1_raw)
            logger.info(f"Part1: {len(part1['plan'])} days OK")

            # Part 2: Days 11-20 (chain part1)
            messages2 = [
                {"role": "system", "content": "You are a fitness expert..."},
                {"role": "user", "content": self.firstpart_workout_prompt_template.replace("INPUT_JSON_HERE", user_text).replace("INPUT_JSON_RESPONSE_SCHEMA", response_schema)},
                {"role": "assistant", "content": part1_raw},
                {"role": "user", "content": self.secondpart_workout_prompt_template.replace("INPUT_JSON_HERE", user_text).replace("INPUT_JSON_RESPONSE_SCHEMA", response_schema)}
            ]
            part2_raw = self._call_api_messages(messages2)
            part2 = json.loads(part2_raw)
            logger.info(f"Part2: {len(part2['plan'])} days OK")

            # Part 3: Days 21-30 (chain part1+2)
            messages3 = messages2 + [
                {"role": "assistant", "content": part2_raw},
                {"role": "user", "content": self.thirdpart_workout_prompt_template.replace("INPUT_JSON_HERE", user_text).replace("INPUT_JSON_RESPONSE_SCHEMA", response_schema)}
            ]
            part3_raw = self._call_api_messages(messages3)
            part3 = json.loads(part3_raw)
            logger.info(f"Part3: {len(part3['plan'])} days OK")

            # MERGE & RETURN
            full_plan = self.merge_workout_parts(part1, part2, part3)
            full_json = self.get_minified_json(json.dumps(full_plan))  # Minified string
            logger.info(f"FULL PLAN: 30 days merged!")
            return full_json

        except Exception as e:
            logger.error(f"Full plan gen failed: {e}")
            error_str = str(e)
            if "404" in error_str:
                raise Exception("The AI service is currently unavailable. Please try again later.")
            raise Exception(f"AI Service Error: {str(e)}")
        
    def _call_api(self, user_text: str, prompt_template: str, is_first: bool = False) -> str:
        """Helper: Single API call with schema."""
        # prompt = prompt_template.replace("INPUT_JSON_HERE", user_text)
        # Remove schema placeholder if using response_format (prompts now schema-free)
        # prompt = prompt.replace("INPUT_JSON_RESPONSE_SCHEMA", "")
        
        # messages = [
        #     {"role": "system", "content": "You are a fitness expert who creates personalized workout plans."},
        #     {"role": "user", "content": prompt}
        # ]
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=prompt_template,
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        
        # DIAGNOSTIC LOGGING:
        logger.info(f"=== API RESPONSE DEBUG ===")
        logger.info(f"Content type: {type(content)}")
        logger.info(f"Content is None: {content is None}")
        logger.info(f"Content length: {len(content) if content else 0}")
        logger.info(f"First 500 chars: {content[:500] if content else 'EMPTY/NONE'}")
        logger.info(f"Full response object: {response}")
        
        if content.strip().startswith('```'):
            # Remove ```json or ``` from start and ``` from end
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]  # Remove ```json
            elif content.startswith('```'):
                content = content[3:]   # Remove ```
            
            if content.endswith('```'):
                content = content[:-3]  # Remove trailing ```
            
            content = content.strip()
            logger.info(f"Stripped markdown wrapper. New length: {len(content)}")
    
        minified = self.get_minified_json(content)
        logger.info(f"API Response: {minified[:200]}...")  # Log snippet
        return minified

    def _call_api_messages(self, messages: list) -> str:
        """Helper for chained calls."""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            # response_format=self.json_response_schema_template,  # ENABLED!
            temperature=0.1
        )
        content = response.choices[0].message.content
        
        # DIAGNOSTIC LOGGING:
        logger.info(f"=== API RESPONSE DEBUG ===")
        logger.info(f"Content type: {type(content)}")
        logger.info(f"Content is None: {content is None}")
        logger.info(f"Content length: {len(content) if content else 0}")
        logger.info(f"First 500 chars: {content[:500] if content else 'EMPTY/NONE'}")
        logger.info(f"Full response object: {response}")
        
        if content.strip().startswith('```'):
            # Remove ```json or ``` from start and ``` from end
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]  # Remove ```json
            elif content.startswith('```'):
                content = content[3:]   # Remove ```
            
            if content.endswith('```'):
                content = content[:-3]  # Remove trailing ```
            
            content = content.strip()
            logger.info(f"Stripped markdown wrapper. New length: {len(content)}")
        
        return self.get_minified_json(content)

    async def get_sample_ai_json_response(self) -> str:
        # i want to add a delay here for 1 min
        await asyncio.sleep(20)
        return self.sample_ai_json_response