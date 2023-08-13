# from bs4 import BeautifulSoup
# from scrapingant_client import ScrapingAntClient

# Define URL with a dynamic web content
# url = "https://kami4ka.github.io/dynamic-website-example/"

# # Create a ScrapingAntClient instance
# client = ScrapingAntClient(token='6631728ab8764f12841e318607308104')

# # Get the HTML page rendered content
# page_content = client.general_request(url).content

# # Parse content with BeautifulSoup
# soup = BeautifulSoup(page_content)
# print(soup.find(id="test").get_text())

def levenshtein_distance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for index2, char2 in enumerate(s2):
        new_distances = [index2 + 1]
        for index1, char1 in enumerate(s1):
            if char1 == char2:
                new_distances.append(distances[index1])
            else:
                new_distances.append(1 + min((distances[index1], distances[index1 + 1], new_distances[-1])))
        distances = new_distances

    return distances[-1]

def is_similar_name(name1, name2, max_distance=2):
    distance = levenshtein_distance(name1.lower(), name2.lower())
    return distance <= max_distance



def main():
    name1 = input("Enter name 1: ")
    name2 = input("Enter name 2: ")
    print(f"{name1} and {name2} are similar names: {is_similar_name(name1, name2)}")


if __name__ == "__main__":
    main()

