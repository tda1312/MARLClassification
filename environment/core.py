import torch as th
import torch.nn as nn


def step(agents: list, img: th.Tensor, max_it: int, softmax: nn.Softmax):
    for a in agents:
        a.new_img()

    for t in range(max_it):
        for a in agents:
            a.step(img)
        for a in agents:
            a.step_finished()

    q = th.zeros(10)
    probas = th.tensor([0.])
    for a in agents:
        pred, proba = a.predict()
        probas += proba
        q += pred

    q = q / len(agents)
    probas = probas / len(agents)

    return softmax(q), probas
