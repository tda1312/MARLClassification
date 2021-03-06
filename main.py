from environment.observation import obs_MNIST
from environment.transition import trans_MNIST
from environment.agent import Agent
from environment.core import step, detailled_step
from networks.models import ModelsUnion
import torch as th
from torch.nn import Softmax, MSELoss, NLLLoss
from data.mnist import load_mnist
from tqdm import tqdm
from math import ceil
import matplotlib.pyplot as plt
from random import randint


def test_MNIST_transition():
    a_1 = th.tensor([1., 0.])
    a_2 = th.tensor([0., 1.])
    a_3 = th.tensor([-1., 0.])
    a_4 = th.tensor([0., -1.])

    print("First test :")
    pos_1 = th.tensor([[0., 0.]])
    print(trans_MNIST(pos_1, a_1, 5, 28))
    print(trans_MNIST(pos_1, a_2, 5, 28))
    print(trans_MNIST(pos_1, a_3, 5, 28))
    print(trans_MNIST(pos_1, a_4, 5, 28))
    print()

    print("Snd test")
    pos_2 = th.tensor([[22., 22.]])
    print(trans_MNIST(pos_2, a_1, 5, 28))
    print(trans_MNIST(pos_2, a_2, 5, 28))
    print(trans_MNIST(pos_2, a_3, 5, 28))
    print(trans_MNIST(pos_2, a_4, 5, 28))


def test_MNIST_obs():
    img = th.arange(0, 28 * 28).view(1, 28, 28)

    print(img)
    print()

    pos = th.tensor([[2, 2]])

    print(obs_MNIST(img, pos, 4))
    print()

    try:
        pos_fail = th.tensor([[-1., -1.]])
        print(obs_MNIST(img, pos_fail, 4))
    except Exception as e:
        print(e)

    try:
        pos_fail = th.tensor([[24., 26.]])
        print(obs_MNIST(img, pos_fail, 4))
    except Exception as e:
        print(e)


def test_agent_step():
    ag = []

    nb_class = 10
    img_size = 28
    n = 16
    f = 5
    n_m = 8
    d = 2
    action_size = 2
    batch_size = 1

    m = ModelsUnion(n, f, n_m, d, action_size, nb_class)

    a1 = Agent(ag, m, n, f, n_m, img_size, action_size, batch_size, obs_MNIST, trans_MNIST)
    a2 = Agent(ag, m, n, f, n_m, img_size, action_size, batch_size, obs_MNIST, trans_MNIST)
    a3 = Agent(ag, m, n, f, n_m, img_size, action_size, batch_size, obs_MNIST, trans_MNIST)

    ag.append(a1)
    ag.append(a2)
    ag.append(a3)

    img = th.rand(batch_size, 28, 28)

    for a in ag:
        a.step(img, True)
    for a in ag:
        a.step_finished()

    print(a1.get_t_msg())


def test_core_step():
    ag = []

    nb_class = 10
    img_size = 28
    n = 16
    f = 5
    n_m = 8
    d = 2
    action_size = 4

    batch_size = 2

    m = ModelsUnion(n, f, n_m, d, action_size, nb_class)

    a1 = Agent(ag, m, n, f, n_m, img_size, action_size, batch_size, obs_MNIST, trans_MNIST)
    a2 = Agent(ag, m, n, f, n_m, img_size, action_size, batch_size, obs_MNIST, trans_MNIST)
    a3 = Agent(ag, m, n, f, n_m, img_size, action_size, batch_size, obs_MNIST, trans_MNIST)

    ag.append(a1)
    ag.append(a2)
    ag.append(a3)

    img = th.rand(batch_size, 28, 28)
    c = th.zeros(batch_size, 10)
    c[:, 5] = 1

    sm = Softmax(dim=1)

    mse = MSELoss()

    params = []
    for n in m.get_networks():
        params += n.parameters()
    optim = th.optim.SGD(params, lr=1e-4)

    nb_epoch = 10

    for e in range(nb_epoch):
        optim.zero_grad()
        pred, proba = step(ag, img, 5, sm, False, False, 10)
        r = mse(pred, c)

        Nr = 1
        loss = (th.log(proba) * r.detach() + r) / Nr
        loss = loss.sum() / batch_size

        loss.backward()
        optim.step()

    for n in m.get_networks():
        if hasattr(n, 'seq_lin'):
            if n.seq_lin[0].weight.grad is None:
                print(n)
            else:
                print(n.seq_lin[0].weight.grad)
        elif hasattr(n, "lstm"):
            if n.lstm.weight_hh_l0.grad is None:
                print(n)
            else:
                print(n.lstm.weight_hh_l0.grad)


def train_mnist():
    ag = []

    nb_class = 10
    img_size = 28
    n = 64
    f = 7
    n_m = 12
    d = 2
    nb_action = 4
    batch_size = 64
    t = 7
    nr = 1

    cuda = True

    #m = ModelsUnion(n, f, n_m, d, nb_action, nb_class, test_mnist())
    m = ModelsUnion(n, f, n_m, d, nb_action, nb_class)

    a1 = Agent(ag, m, n, f, n_m, img_size, nb_action, batch_size, obs_MNIST, trans_MNIST)
    a2 = Agent(ag, m, n, f, n_m, img_size, nb_action, batch_size, obs_MNIST, trans_MNIST)
    a3 = Agent(ag, m, n, f, n_m, img_size, nb_action, batch_size, obs_MNIST, trans_MNIST)

    ag.append(a1)
    ag.append(a2)
    ag.append(a3)

    if cuda:
        for a in ag:
            a.cuda()

    sm = Softmax(dim=-1)

    criterion = MSELoss()
    if cuda:
        criterion.cuda()

    params = []
    for net in m.get_networks():
        if cuda:
            net.cuda()
        params += list(net.parameters())

    optim = th.optim.Adam(params, lr=1e-3)

    nb_epoch = 10

    (x_train, y_train), (x_valid, y_valid), (x_test, y_test) = load_mnist()
    x_train, y_train = x_train[:10000], y_train[:10000]

    nb_batch = ceil(x_train.size(0) / batch_size)

    loss_v = []
    acc = []

    for e in range(nb_epoch):
        sum_loss = 0

        for net in m.get_networks():
            net.train()

        grad_norm_cnn = []
        grad_norm_pred = []

        random_walk = e < 5

        for i in tqdm(range(nb_batch)):
            i_min = i * batch_size
            i_max = (i + 1) * batch_size
            i_max = i_max if i_max < x_train.size(0) else x_train.size(0)

            losses = []

            for k in range(nr):

                x, y = x_train[i_min:i_max, :, :], y_train[i_min:i_max]

                if cuda:
                    x, y = x.cuda(), y.cuda()

                pred, log_probas = step(ag, x, t, sm, cuda, random_walk, nb_class)

                # Sum on agent dimension
                proba_per_image = log_probas.sum(dim=0)

                y_eye = th.eye(nb_class)[y]
                if cuda:
                    y_eye = y_eye.cuda()

                r = -criterion(pred, y_eye)

                # Mean on image batch
                l = (proba_per_image * r.detach() + r).mean(dim=0).view(-1)

                losses.append(l)

            loss = -th.cat(losses).sum() / nr

            optim.zero_grad()
            loss.backward()
            optim.step()

            sum_loss += loss.item()

            grad_norm_cnn.append(m.get_networks()[0].seq_lin[0].weight.grad.norm())
            grad_norm_pred.append(m.get_networks()[-1].seq_lin[0].weight.grad.norm())

        sum_loss /= nb_batch

        print("Epoch %d, loss = %f" % (e, sum_loss))
        print("grad_cnn_norm_mean = %f, grad_pred_norm_mean = %f" % (sum(grad_norm_cnn) / len(grad_norm_cnn), sum(grad_norm_pred) / len(grad_norm_pred)))
        print("CNN_el = %d, Pred_el = %d" % (m.get_networks()[0].seq_lin[0].weight.grad.nelement(), m.get_networks()[-1].seq_lin[0].weight.grad.nelement()))

        nb_correct = 0

        nb_batch_valid = ceil(x_valid.size(0) / batch_size)

        for net in m.get_networks():
            net.eval()

        with th.no_grad():
            for i in tqdm(range(nb_batch_valid)):
                i_min = i * batch_size
                i_max = (i + 1) * batch_size
                i_max = i_max if i_max < x_valid.size(0) else x_valid.size(0)

                x, y = x_valid[i_min:i_max, :, :].cuda(), y_valid[i_min:i_max].cuda()

                pred, proba = step(ag, x, t, sm, cuda, random_walk, nb_class)

                nb_correct += (pred.argmax(dim=1) == y).sum().item()

            nb_correct /= x_valid.size(0)

            acc.append(nb_correct)
            loss_v.append(sum_loss)
            print("Epoch %d, accuracy = %f" % (e, nb_correct))

    plt.plot(acc, "b", label="accuracy")
    plt.plot(loss_v, "r", label="criterion value")
    plt.xlabel("Epoch")
    plt.title("MARL Classification f=%d, n=%d, n_m=%d, d=%d, T=%d" % (f, n, n_m, d, t))
    plt.legend()
    plt.show()

    viz(ag, x_test[randint(0, x_test.size(0)-1)], t, sm, f)


def viz(agents: list, one_img: th.Tensor, max_it: int, softmax: Softmax, f: int):
    pred, pos = detailled_step(agents, one_img.unsqueeze(0).cuda(), max_it, softmax, True, 10)

    plt.imshow(one_img)
    plt.show()

    print(pos)

    tmp = th.zeros(28, 28) - 1
    for t in range(max_it):

        for i in range(len(agents)):
            tmp[pos[i][t][0]:pos[i][t][0]+f, pos[i][t][1]:pos[i][t][1]+f] = \
                one_img[pos[i][t][0]:pos[i][t][0]+f, pos[i][t][1]:pos[i][t][1]+f]

        plt.imshow(tmp, cmap='gray_r')
        plt.title("Step = %d" % t)
        plt.show()


if __name__ == "__main__":
    #test_MNIST_transition()
    #test_MNIST_obs()

    #test_agent_step()
    #test_core_step()

    train_mnist()
