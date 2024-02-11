from PIL import Image, ImageDraw

def create_omr_template(output_path, num_questions, num_choices):
    # Dimensions of the OMR sheet
    sheet_width = 600
    sheet_height = 800
    margin = 20
    question_spacing = 40
    choice_spacing = 20

    # Create a blank white image
    img = Image.new("RGB", (sheet_width, sheet_height), "white")
    draw = ImageDraw.Draw(img)

    # Function to draw a question with choices
    def draw_question(x, y, num_choices):
        # Draw question text
        draw.text((x, y), "Question {}".format(i + 1), fill="black")

        # Draw choices
        for j in range(num_choices):
            choice_x = x + (j + 1) * choice_spacing
            draw.rectangle([choice_x, y + 20, choice_x + 15, y + 35], outline="black")

    # Draw multiple questions with choices
    for i in range(num_questions):
        question_x = margin
        question_y = margin + i * question_spacing
        draw_question(question_x, question_y, num_choices)

    # Save the template image
    img.save(output_path)

# Example: Create a template with 5 questions, each having 4 choices
create_omr_template("omr_template.png", num_questions=5, num_choices=4)
