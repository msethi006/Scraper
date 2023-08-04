import tqdm
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import os
from helper import scraper_for_keto_news,scraper_for_reuters
import warnings
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", message="Token indices sequence length is longer than the specified maximum sequence length")
os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = '1'
from transformers import logging
logging.set_verbosity_error()

def calculate_sentiment_score(predicted_probs,predicted_class):
    if predicted_class == 0:
        return abs(predicted_probs[0][1] - predicted_probs[0][2])
    elif predicted_class == 1:
        return predicted_probs[0][1]
    elif predicted_class == 2:
        return -predicted_probs[0][2]



def process_chunks(input_text):
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=max_seq_length)
    # Perform inference
    outputs = model(**inputs)
    # Get the predicted class probabilities for each label
    predicted_probs = torch.softmax(outputs.logits, dim=1)
    return predicted_probs.tolist()
def to_four_digit_float(num):
    return round(num,4)

if __name__ == '__main__':
    total_links = []
    df = pd.DataFrame(columns =['Publisher','Link','Article Title','Date Time','Article Content',
                                    'Keywords Present','Sentiment','Sentiment Score'])
    while True:
        article_data = scraper_for_keto_news()
        link_list = []
        title_list = []
        text_list = []
        keyword_list = []
        date_time_list = []
        publisher = ['Kito News'] 
        counter = 0

        for link in article_data:
            if link not in total_links:
                counter+=1
                total_links.append(link)
                link_list.append(link)
                title_list.append(article_data[link]['Title'])
                date_time_list.append(article_data[link]['Date & Time'])
                text_list.append(article_data[link]['Article Text'])
                keyword_list.append(article_data[link]['Keywords Present in Article Text'])
                
                
            else:
                continue
        df2 = pd.DataFrame({'Publisher': publisher * counter,
                                    'Link':link_list,
                                'Article Title':title_list,
                                'Date Time': date_time_list,
                                'Article Content':text_list,
                                'Keywords Present':keyword_list})
        df2['Date Time'] = pd.to_datetime(df2['Date Time'], format='%A %B %d, %Y %H:%M')
        df = pd.concat([df,df2])

        article_data = scraper_for_reuters()
        link_list = []
        title_list = []
        text_list = []
        keyword_list = []
        date_time_list = []
        publisher = ['Reuters'] 
        counter = 0

        for link in article_data:
            if link not in total_links:
                counter+=1
                total_links.append(link)
                link_list.append(link)
                title_list.append(article_data[link]['Title'])
                date_time_list.append(article_data[link]['Date & Time'])
                text_list.append(article_data[link]['Article Text'])
                keyword_list.append(article_data[link]['Keywords Present in Article Text'])
                
            else:
                continue
        df2 = pd.DataFrame({'Publisher': publisher * counter,
                            'Link':link_list,
                        'Article Title':title_list,
                        'Date Time': date_time_list,
                        'Article Content':text_list,
                        'Keywords Present':keyword_list})
        df2['Date Time'] = pd.to_datetime(df2['Date Time'], format='%B %d, %Y %I:%M %p %Z')
        df = pd.concat([df,df2])

        df.sort_values(by='Keywords Present', inplace=True)
        df.sort_values(by='Keywords Present',key=lambda x: x.str.len(),ascending=True,inplace=True)
        
        df.reset_index(inplace=True)
        if 'index' in df.columns : df.drop(['index'],axis=1, inplace=True)

        model_directory = os.path.join(os.getcwd(), "checkpoint-4860")
        # Load the tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_directory)
        model = AutoModelForSequenceClassification.from_pretrained(model_directory)
        map1 = {'neutral':0,'positive':1,'negative':2}
        map2 = {b:a for a,b in map1.items()}
        max_seq_length = tokenizer.model_max_length
        for index in tqdm.tqdm(df[df['Sentiment'].isnull()].index,desc="Running AI Model"):
            text = df.iloc[index]['Article Title'] + df.iloc[index]['Article Content']
            inputs = tokenizer(text, return_tensors="pt") 
            if inputs['input_ids'].shape[1] < max_seq_length:

                outputs = model(**inputs)
                # Get the predicted class label (for classification tasks)
                predicted_probs = torch.softmax(outputs.logits, dim=1)
                # Get the predicted class 
                predicted_class = torch.argmax(predicted_probs, dim=1).item()
                sent_score = calculate_sentiment_score(predicted_probs,predicted_class)
                df.iloc[index]['Sentiment Score'] = to_four_digit_float(sent_score.detach().item())
                df.iloc[index]['Sentiment'] =map2[predicted_class]
            # If the text is longer than the model's maximum sequence length, process it in chunks
            if inputs['input_ids'].shape[1] >= max_seq_length:
                chunks = [text[i:i + max_seq_length] for i in range(0, len(text), max_seq_length)]
                predicted_probs_list = [process_chunks(chunk) for chunk in chunks]
                # Combine the predicted probabilities from all chunks
                combined_probs = torch.tensor(predicted_probs_list).mean(dim=0)
                predicted_probs = torch.softmax(combined_probs, dim=1)
                # Get the predicted class label
                predicted_class = torch.argmax(predicted_probs, dim=1).item()
                sent_score = calculate_sentiment_score(predicted_probs,predicted_class)
                df.iloc[index]['Sentiment Score'] = to_four_digit_float(sent_score.detach().item())
                df.iloc[index]['Sentiment'] =map2[predicted_class]

        df.to_csv('results.csv',index =False)

        with open('scores.txt','w') as f1:
            for i in range(len(df)):
                itime = str(df.iloc[i]['Date Time'].strftime('%H:%M'))
                idate = str(df.iloc[i]['Date Time'].date())
                f1.write(f"{df.iloc[i]['Sentiment Score']} {idate} {itime} {df.iloc[i]['Keywords Present']} \n")